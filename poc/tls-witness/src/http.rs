//! The HTTP/1.1 exchanges of a session: built byte for byte by the prover,
//! parsed from the revealed transcript by the verifier.

use std::{collections::BTreeMap, ops::Range};

use anyhow::{Result, anyhow, bail};
use serde::Deserialize;
use serde_json::value::RawValue;

/// Headers the prover sets itself; a request file may not supply them.
const PROVER_HEADERS: [&str; 8] = [
    "host",
    "content-length",
    "connection",
    "authorization",
    "x-api-key",
    "x-job-id",
    "transfer-encoding",
    "accept-encoding",
];

#[derive(Deserialize, Clone)]
#[serde(deny_unknown_fields)]
pub struct RequestFile {
    pub method: String,
    pub host: String,
    pub path: String,
    #[serde(default)]
    pub headers: BTreeMap<String, String>,
    #[serde(skip)]
    pub ordered_headers: Vec<(String, String)>,
    #[serde(skip)]
    pub raw_body: Option<Vec<u8>>,
    /// Kept as the exact bytes in the file; these are the bytes sent and hashed.
    #[serde(default)]
    pub body: Option<Box<RawValue>>,
}

impl RequestFile {
    pub fn body_bytes(&self) -> &[u8] {
        if let Some(body) = &self.raw_body {
            return body;
        }
        self.body.as_ref().map_or(&[], |b| b.get().as_bytes())
    }
}

pub struct BuiltRequest {
    pub bytes: Vec<u8>,
    /// The `Authorization` header value; the only sent bytes left unrevealed.
    pub auth_value: Range<usize>,
}

fn is_token(s: &str) -> bool {
    !s.is_empty()
        && s.bytes()
            .all(|b| b.is_ascii_alphanumeric() || b"!#$%&'*+-.^_`|~".contains(&b))
}

fn is_field_value(s: &str) -> bool {
    s.bytes().all(|b| b == b'\t' || (b' '..=b'~').contains(&b))
}

/// `keep_alive`: another request follows on this connection; otherwise the
/// server is asked to close after its response.
pub fn build_request(
    req: &RequestFile,
    api_key: &str,
    job_id: &str,
    keep_alive: bool,
    credential_header: crate::CredentialHeader,
) -> Result<BuiltRequest> {
    if !is_token(&req.method) {
        bail!("request method {:?} is not an HTTP token", req.method);
    }
    if !req.path.starts_with('/') || !req.path.bytes().all(|b| (b'!'..=b'~').contains(&b)) {
        bail!("request path must start with '/' and contain no spaces or control bytes");
    }
    if !is_token(&req.host.replace(':', "")) {
        bail!("request host {:?} is not a valid host", req.host);
    }
    if !is_field_value(api_key) || api_key.is_empty() {
        bail!("credential is empty or contains bytes not allowed in a header");
    }
    let body = req.body_bytes();

    let mut out = Vec::new();
    out.extend_from_slice(
        format!(
            "{} {} HTTP/1.1\r\nHost: {}\r\n",
            req.method, req.path, req.host
        )
        .as_bytes(),
    );
    for (name, value) in req
        .headers
        .iter()
        .chain(req.ordered_headers.iter().map(|(k, v)| (k, v)))
    {
        if !is_token(name) || !is_field_value(value) {
            bail!("request header {name:?} has an invalid name or value");
        }
        if PROVER_HEADERS.contains(&name.to_ascii_lowercase().as_str()) {
            bail!(
                "request header {name:?} is set by the prover and may not be in the request file"
            );
        }
        out.extend_from_slice(format!("{name}: {value}\r\n").as_bytes());
    }
    out.extend_from_slice(format!("Accept-Encoding: identity\r\n{}: ", credential_header.as_str()).as_bytes());
    let start = out.len();
    out.extend_from_slice(credential_header.prefix().as_bytes());
    out.extend_from_slice(api_key.as_bytes());
    let auth_value = start..out.len();
    out.extend_from_slice(
        format!(
            "\r\nX-Job-Id: {job_id}\r\nContent-Length: {}\r\nConnection: {}\r\n\r\n",
            body.len(),
            if keep_alive { "keep-alive" } else { "close" }
        )
        .as_bytes(),
    );
    out.extend_from_slice(body);
    Ok(BuiltRequest {
        bytes: out,
        auth_value,
    })
}

pub struct ParsedRequest {
    pub method: String,
    pub path: String,
    pub host: String,
    pub job_id: String,
    pub body: Range<usize>,
    pub auth_value: Option<Range<usize>>,
    pub credential_header: crate::CredentialHeader,
    pub forwarded_headers_sha256: String,
}

fn offset(buf: &[u8], part: &[u8]) -> Range<usize> {
    let start = part.as_ptr() as usize - buf.as_ptr() as usize;
    start..start + part.len()
}

fn single<'a>(headers: &[httparse::Header<'a>], name: &str) -> Result<Option<&'a [u8]>> {
    let mut found = headers.iter().filter(|h| h.name.eq_ignore_ascii_case(name));
    let first = found.next().map(|h| h.value);
    if found.next().is_some() {
        bail!("header {name} appears more than once");
    }
    Ok(first)
}

fn text(value: &[u8], name: &str) -> Result<String> {
    String::from_utf8(value.to_vec()).map_err(|_| anyhow!("header {name} is not UTF-8"))
}

/// Parses the full sent transcript as one or more requests in a row, each
/// with a `Content-Length` body; the last ends at the end of the transcript.
/// Ranges are into `buf`.
pub fn parse_requests(buf: &[u8]) -> Result<Vec<ParsedRequest>> {
    parse_requests_with_policy(buf, false)
}

/// Operator sessions may contain only the headers the router constructs.
pub fn parse_router_requests(buf: &[u8]) -> Result<Vec<ParsedRequest>> {
    parse_requests_with_policy(buf, true)
}

fn parse_requests_with_policy(buf: &[u8], router: bool) -> Result<Vec<ParsedRequest>> {
    let mut out = Vec::new();
    let mut at = 0;
    while at < buf.len() || out.is_empty() {
        let req = parse_request_at(buf, at, router)
            .map_err(|e| e.context(format!("request {}", out.len() + 1)))?;
        at = req.body.end;
        out.push(req);
    }
    Ok(out)
}

/// The request starting at `at`, which ends at its Content-Length.
fn parse_request_at(buf: &[u8], at: usize, router: bool) -> Result<ParsedRequest> {
    let mut headers = [httparse::EMPTY_HEADER; 64];
    let mut req = httparse::Request::new(&mut headers);
    let head_len = match req.parse(&buf[at..])? {
        httparse::Status::Complete(n) => n,
        httparse::Status::Partial => bail!("request head is incomplete"),
    };
    let headers = req.headers;
    if router {
        for header in headers.iter() {
            let name = header.name.to_ascii_lowercase();
            if !matches!(name.as_str(), "host" | "authorization" | "x-api-key" | "x-job-id"
                | "content-length" | "connection" | "accept-encoding" | "content-type")
                && !name.starts_with("x-client-")
            {
                bail!("router request contains forbidden header {}", header.name);
            }
        }
        for name in ["host", "x-job-id", "content-length"] {
            single(headers, name)?.ok_or_else(|| anyhow!("router request has no {name} header"))?;
        }
        for (name, expected) in [("accept-encoding", b"identity".as_slice()), ("connection", b"close".as_slice())] {
            if single(headers, name)? != Some(expected) {
                bail!("router request requires {name}: {}", String::from_utf8_lossy(expected));
            }
        }
    }
    if single(headers, "transfer-encoding")?.is_some() {
        bail!("request uses Transfer-Encoding; only Content-Length bodies are accepted");
    }
    let authorization = single(headers, "authorization")?;
    let api_key = single(headers, "x-api-key")?;
    let (credential_header, credential_value) = match (authorization, api_key) {
        (Some(value), None) => (crate::CredentialHeader::Authorization, value),
        (None, Some(value)) => (crate::CredentialHeader::XApiKey, value),
        (Some(_), Some(_)) => bail!("ambiguous credential headers: authorization and x-api-key"),
        (None, None) => bail!("request has no supported credential header"),
    };
    if credential_value.is_empty() { bail!("credential header value is empty"); }
    let host = single(headers, "host")?.ok_or_else(|| anyhow!("request has no Host header"))?;
    let job_id =
        single(headers, "x-job-id")?.ok_or_else(|| anyhow!("request has no X-Job-Id header"))?;
    let content_length = match single(headers, "content-length")? {
        Some(v) => content_length(v)?,
        None => 0,
    };
    let body = at + head_len..at + head_len + content_length;
    if buf.len() < body.end {
        bail!(
            "request body is {} bytes but Content-Length says {content_length}",
            buf.len() - body.start
        );
    }
    let job_id = text(job_id, "X-Job-Id")?;
    if job_id.is_empty() {
        bail!("X-Job-Id is empty");
    }
    Ok(ParsedRequest {
        method: req.method.unwrap_or_default().to_string(),
        path: req.path.unwrap_or_default().to_string(),
        host: text(host, "Host")?,
        job_id,
        body,
        auth_value: Some(offset(buf, credential_value)),
        credential_header,
        forwarded_headers_sha256: forwarded_hash(
            &headers
                .iter()
                .map(|h| Ok((h.name.to_ascii_lowercase(), text(h.value, h.name)?)))
                .collect::<Result<Vec<_>>>()?,
        ),
    })
}

#[derive(Clone)]
pub struct ParsedResponse {
    pub content_type: Option<String>,
    pub reserved_receipt: bool,
    pub status: u16,
    pub chunked: bool,
    pub body: Vec<u8>,
}

/// Parses the full received transcript as one response after another; only
/// the last may run to the server's close.
pub fn parse_responses(buf: &[u8]) -> Result<Vec<ParsedResponse>> {
    let mut out = Vec::new();
    let mut at = 0;
    while at < buf.len() || out.is_empty() {
        let (response, used) = parse_response_at(&buf[at..], true)
            .map_err(|e| e.context(format!("response {}", out.len() + 1)))?;
        at += used;
        out.push(response);
    }
    Ok(out)
}

/// The response at the start of `buf` and the bytes it takes. Bytes after it
/// are left for the caller. With `closed`, a body without framing runs to
/// the end of `buf`; without, it is incomplete.
pub fn parse_response_at(buf: &[u8], closed: bool) -> Result<(ParsedResponse, usize)> {
    let mut headers = [httparse::EMPTY_HEADER; 64];
    let mut resp = httparse::Response::new(&mut headers);
    let head_len = match resp.parse(buf)? {
        httparse::Status::Complete(n) => n,
        httparse::Status::Partial => bail!(
            "response is truncated: {} bytes, head incomplete",
            buf.len()
        ),
    };
    let status = resp.code.unwrap_or_default();
    let headers = resp.headers;
    if (100..200).contains(&status) {
        bail!("informational {status} responses are not supported");
    }
    let rest = &buf[head_len..];
    let chunked = match single(headers, "transfer-encoding")? {
        Some(v) => {
            let v = text(v, "Transfer-Encoding")?.to_ascii_lowercase();
            if v.trim() != "chunked" {
                bail!("unsupported Transfer-Encoding {v:?}");
            }
            true
        }
        None => false,
    };
    let (body, used) = if chunked {
        dechunk(rest)?
    } else if status == 204 || status == 304 {
        (Vec::new(), 0)
    } else if let Some(v) = single(headers, "content-length")? {
        let n = content_length(v)?;
        if rest.len() < n {
            bail!("response is truncated: body {} of {n} bytes", rest.len());
        }
        (rest[..n].to_vec(), n)
    } else if closed {
        (rest.to_vec(), rest.len())
    } else {
        bail!("the body ends when the server closes, and it had not closed");
    };
    Ok((
        ParsedResponse {
            content_type: single(headers, "content-type")?
                .map(|v| text(v, "Content-Type"))
                .transpose()?,
            reserved_receipt: headers
                .iter()
                .any(|h| h.name.eq_ignore_ascii_case("x-witness-receipt")),
            status,
            chunked,
            body,
        },
        head_len + used,
    ))
}

/// Content-Length is one or more ASCII decimal digits, never a signed integer.
pub(crate) fn content_length(value: &[u8]) -> Result<usize> {
    if value.is_empty() || !value.iter().all(u8::is_ascii_digit) {
        bail!("Content-Length must contain only decimal digits");
    }
    Ok(std::str::from_utf8(value)?.parse()?)
}

/// Decodes a chunked body; returns the body and the bytes consumed,
/// including the last chunk, trailers and final CRLF.
pub(crate) fn dechunk(data: &[u8]) -> Result<(Vec<u8>, usize)> {
    let line = |at: usize| -> Result<(&[u8], usize)> {
        let end = data[at..]
            .windows(2)
            .position(|w| w == b"\r\n")
            .ok_or_else(|| anyhow!("chunked response is truncated"))?;
        Ok((&data[at..at + end], at + end + 2))
    };
    let mut body = Vec::new();
    let mut at = 0;
    loop {
        let (size_line, next) = line(at)?;
        let size_text = size_line.split(|&b| b == b';').next().unwrap_or_default();
        let size = std::str::from_utf8(size_text)
            .ok()
            .and_then(|s| usize::from_str_radix(s.trim(), 16).ok())
            .ok_or_else(|| anyhow!("invalid chunk size line"))?;
        at = next;
        if size == 0 {
            loop {
                let (trailer, next) = line(at)?;
                at = next;
                if trailer.is_empty() {
                    return Ok((body, at));
                }
            }
        }
        if data.len() < at + size + 2 {
            bail!("chunked response is truncated");
        }
        body.extend_from_slice(&data[at..at + size]);
        if &data[at + size..at + size + 2] != b"\r\n" {
            bail!("chunk is not followed by CRLF");
        }
        at += size + 2;
    }
}

/// The body bytes readable so far from a response still arriving, as ranges
/// of `buf`: none until the head is complete; then the body up to its
/// Content-Length or to the end, or for a chunked body the data of each chunk
/// so far, including a partial last one. A streaming prover writes these to
/// disk as they arrive; the complete body is still taken from
/// [`parse_response_at`] once the response is complete.
#[allow(clippy::single_range_in_vec_init)] // one range, the identity body
pub fn body_so_far(buf: &[u8]) -> Vec<Range<usize>> {
    let mut headers = [httparse::EMPTY_HEADER; 64];
    let mut resp = httparse::Response::new(&mut headers);
    let Ok(httparse::Status::Complete(head_len)) = resp.parse(buf) else {
        return Vec::new();
    };
    let header = |name: &str| {
        resp.headers
            .iter()
            .find(|h| h.name.eq_ignore_ascii_case(name))
            .and_then(|h| std::str::from_utf8(h.value).ok())
            .map(|v| v.trim().to_ascii_lowercase())
    };
    if header("transfer-encoding").as_deref() != Some("chunked") {
        let end = match header("content-length").and_then(|v| v.parse::<usize>().ok()) {
            Some(n) => (head_len + n).min(buf.len()),
            None => buf.len(),
        };
        return vec![head_len..end];
    }
    let mut out = Vec::new();
    let mut at = head_len;
    while let Some(eol) = buf[at..].windows(2).position(|w| w == b"\r\n") {
        let size = std::str::from_utf8(&buf[at..at + eol]).ok().and_then(|l| {
            usize::from_str_radix(l.split(';').next().unwrap_or_default().trim(), 16).ok()
        });
        let Some(size) = size.filter(|&n| n > 0) else {
            break;
        };
        let start = at + eol + 2;
        out.push(start..(start + size).min(buf.len()));
        at = start + size + 2;
        if at > buf.len() {
            break;
        }
    }
    out
}

/// An image carried inline in a JSON response body.
pub struct InlineImage {
    pub media_type: String,
    pub bytes: Vec<u8>,
}

/// Every base64 image in a JSON response body, in document order: string
/// values that are `data:<type>;base64,` URLs, and `b64_json` fields, whose
/// type is a sibling `media_type` string if there is one, as OpenRouter's
/// image API sends it, else empty. A body that is not JSON has none.
pub fn inline_images(body: &[u8]) -> Result<Vec<InlineImage>> {
    use base64::Engine as _;
    fn walk<'a>(
        value: &'a serde_json::Value,
        key: Option<&str>,
        sibling_type: &str,
        out: &mut Vec<(String, &'a str)>,
    ) {
        match value {
            serde_json::Value::Object(map) => {
                let media_type = map
                    .get("media_type")
                    .and_then(|v| v.as_str())
                    .unwrap_or_default();
                map.iter()
                    .for_each(|(k, v)| walk(v, Some(k), media_type, out))
            }
            serde_json::Value::Array(items) => items.iter().for_each(|v| walk(v, None, "", out)),
            serde_json::Value::String(s) => {
                if let Some((head, data)) = s
                    .strip_prefix("data:")
                    .and_then(|r| r.split_once(";base64,"))
                {
                    out.push((head.to_string(), data));
                } else if key == Some("b64_json") {
                    out.push((sibling_type.to_string(), s));
                }
            }
            _ => {}
        }
    }
    let Ok(json) = serde_json::from_slice::<serde_json::Value>(body) else {
        return Ok(Vec::new());
    };
    let mut found = Vec::new();
    walk(&json, None, "", &mut found);
    found
        .into_iter()
        .enumerate()
        .map(|(i, (media_type, data))| {
            let bytes = base64::engine::general_purpose::STANDARD
                .decode(data)
                .map_err(|e| anyhow!("inline image {i} is not valid base64: {e}"))?;
            Ok(InlineImage { media_type, bytes })
        })
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn b64_json_takes_its_sibling_media_type() {
        let body = br#"{"data":[{"b64_json":"aGk=","media_type":"image/jpeg"},{"b64_json":"aGk="}],
            "x":{"url":"data:image/png;base64,aGk="}}"#;
        let found = inline_images(body).unwrap();
        let types: Vec<&str> = found.iter().map(|i| i.media_type.as_str()).collect();
        assert_eq!(types, ["image/jpeg", "", "image/png"]);
        assert!(found.iter().all(|i| i.bytes == b"hi"));
    }

    #[test]
    fn body_so_far_follows_chunks_as_they_arrive() {
        let full = b"HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\n\r\n5\r\nhello\r\n6\r\n world\r\n0\r\n\r\n";
        let body = |n: usize| -> Vec<u8> {
            body_so_far(&full[..n])
                .into_iter()
                .flat_map(|r| full[r].to_vec())
                .collect()
        };
        assert_eq!(body(20), b"");
        assert_eq!(body(53), b"hel");
        assert_eq!(body(full.len()), b"hello world");
        let whole = parse_response_at(full, true).unwrap().0.body;
        assert_eq!(body(full.len()), whole);
        for n in 0..=full.len() {
            assert!(whole.starts_with(&body(n)));
        }
    }

    #[test]
    fn framed_response_needs_its_own_end() {
        let chunked =
            b"HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\n\r\n5\r\nhello\r\n0\r\n\r\n";
        let framed = |buf: &[u8]| parse_response_at(buf, false).map(|(r, used)| (r.body, used));
        assert_eq!(framed(chunked).unwrap(), (b"hello".to_vec(), chunked.len()));
        assert!(framed(&chunked[..chunked.len() - 5]).is_err());
        let sized = b"HTTP/1.1 200 OK\r\nContent-Length: 5\r\n\r\nhello";
        assert_eq!(framed(sized).unwrap(), (b"hello".to_vec(), sized.len()));
        assert!(framed(&sized[..sized.len() - 1]).is_err());
        assert!(framed(b"HTTP/1.1 200 OK\r\n\r\nhello").is_err());
    }

    #[test]
    fn sequences_split_by_their_framing() {
        let a = RequestFile {
            method: "POST".into(),
            host: "h.example".into(),
            path: "/x".into(),
            headers: BTreeMap::new(),
            ordered_headers: Vec::new(),
            raw_body: None,
            body: Some(RawValue::from_string("{\"a\":1}".into()).unwrap()),
        };
        let one = build_request(&a, "k1", "job-1", true, crate::CredentialHeader::Authorization).unwrap();
        let two = build_request(&a, "k22", "job-2", false, crate::CredentialHeader::Authorization).unwrap();
        let sent = [one.bytes.clone(), two.bytes.clone()].concat();
        let reqs = parse_requests(&sent).unwrap();
        assert_eq!(reqs.len(), 2);
        assert_eq!(reqs[0].job_id, "job-1");
        assert_eq!(reqs[1].job_id, "job-2");
        assert_eq!(reqs[0].auth_value, Some(one.auth_value.clone()));
        let off = one.bytes.len();
        assert_eq!(
            reqs[1].auth_value,
            Some(two.auth_value.start + off..two.auth_value.end + off)
        );
        assert_eq!(&sent[reqs[1].body.clone()], b"{\"a\":1}");
        assert!(parse_requests(&sent[..sent.len() - 1]).is_err());

        let recv = b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\nhiHTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\n\r\n3\r\nyou\r\n0\r\n\r\nHTTP/1.1 200 OK\r\n\r\nrest";
        let resps = parse_responses(recv).unwrap();
        let bodies: Vec<&[u8]> = resps.iter().map(|r| r.body.as_slice()).collect();
        assert_eq!(bodies, [&b"hi"[..], b"you", b"rest"]);
        let (first, used) = parse_response_at(recv, false).unwrap();
        assert_eq!((first.body.as_slice(), used), (&b"hi"[..], 40));
    }

    /// The saved Phase 4 image response, where the verdict's media type was
    /// empty: `WITNESS_IMAGE_BODY=<response.bin> cargo test -- --ignored`.
    #[test]
    #[ignore]
    fn saved_image_response() {
        let path = std::env::var("WITNESS_IMAGE_BODY").expect("WITNESS_IMAGE_BODY");
        let body = std::fs::read(&path).unwrap();
        for (i, image) in inline_images(&body).unwrap().iter().enumerate() {
            println!(
                "image {i}: media_type {:?}, {} bytes, sha256 {}",
                image.media_type,
                image.bytes.len(),
                crate::record::sha256_hex(&image.bytes)
            );
        }
    }
}

/// JSON array of [lowercase name, value] pairs; ordering and duplicates survive.
pub fn forwarded_hash(headers: &[(String, String)]) -> String {
    let selected: Vec<_> = headers
        .iter()
        .filter(|(n, _)| forwarded(n))
        .map(|(n, v)| (n.to_ascii_lowercase(), v))
        .collect();
    crate::record::sha256_hex(&serde_json::to_vec(&selected).expect("strings"))
}
pub fn forwarded(name: &str) -> bool {
    let name = name.to_ascii_lowercase();
    name == "content-type" || name.starts_with("x-client-")
}
