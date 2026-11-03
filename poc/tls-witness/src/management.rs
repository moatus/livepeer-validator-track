//! Ordinary, unwitnessed HTTPS management exchanges. Neither expanded
//! templates nor response bodies nor credential values are ever persisted.
use std::{collections::BTreeMap, net::SocketAddr, path::Path, time::Duration};
use anyhow::{Result, anyhow, bail};
use serde::Deserialize;
use serde_json::Value;

#[derive(Clone, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Template {
    method: String,
    host: String,
    path: String,
    #[serde(default)]
    headers: BTreeMap<String, String>,
    body: Option<Value>,
    /// JSON pointer into the obtain response. Absent: locally generated key.
    pub credential_field: Option<String>,
    /// Override DNS for the fixture, retaining host certificate validation.
    address: Option<SocketAddr>,
    /// Explicit model for fixture GET jobs, which have no inference body.
    fixture_model: Option<String>,
}

pub fn load(path: &Path) -> Result<Template> {
    let bytes = std::fs::read(path).map_err(|_| anyhow!("cannot read management template"))?;
    serde_json::from_slice(&bytes).map_err(|_| anyhow!("invalid management template"))
}

impl Template {
    /// Read back only the newly obtained key, using the create request's
    /// certified host, management authorization and optional fixture address.
    pub fn key_readback(&self, obtained: &Value) -> Result<Self> {
        let hash = obtained.pointer("/data/hash").and_then(Value::as_str)
            .filter(|h| !h.is_empty() && h.bytes().all(|b| b.is_ascii_alphanumeric() || b"-_".contains(&b)))
            .ok_or_else(|| anyhow!("obtain key hash missing or invalid"))?;
        let mut readback = self.clone();
        readback.method = "GET".into();
        readback.path = format!("{}/{}", self.path.trim_end_matches('/'), hash);
        readback.body = None;
        readback.credential_field = None;
        Ok(readback)
    }

    /// The provider must confirm a positive finite limit no larger than requested.
    pub fn confirms_limit(&self, fields: &Value) -> bool {
        let requested = self.body.as_ref().and_then(|b| b.get("limit")).and_then(Value::as_f64);
        let actual = fields.pointer("/data/limit").and_then(Value::as_f64);
        matches!((requested, actual), (Some(cap), Some(limit))
            if cap.is_finite() && cap > 0.0 && limit.is_finite() && limit > 0.0 && limit <= cap)
    }

    // Keep the local, locally generated-credential fixture path available;
    // OpenRouter obtains must confirm even if an old template omits the flag.
    pub fn requires_byok_confirmation(&self) -> bool {
        self.host.eq_ignore_ascii_case("openrouter.ai")
            || self.body.as_ref().is_some_and(|b| b.get("include_byok_in_limit").is_some())
    }
}

fn expand(text: &str, obtained: &Value, session_name: &str) -> Result<String> {
    let mut out = String::new();
    let mut rest = text;
    // Scan the original template only. Inserted secrets are never interpreted.
    while let Some(i) = rest.find('{') {
        out.push_str(&rest[..i]);
        rest = &rest[i..];
        if rest.starts_with("{session}") {
            out.push_str(session_name);
            rest = &rest[9..];
        } else if rest.starts_with("{env:") || rest.starts_with("{obtain:") {
            let end = rest.find('}').ok_or_else(|| anyhow!("unclosed management substitution"))?;
            let token = &rest[1..end];
            let value = if let Some(name) = token.strip_prefix("env:") {
                if name == "OPENROUTER_API_KEY" { bail!("management template may not load OPENROUTER_API_KEY"); }
                std::env::var(name).map_err(|_| anyhow!("management environment setting missing"))?
            } else {
                obtained.pointer(&token[7..]).and_then(Value::as_str)
                    .ok_or_else(|| anyhow!("management response field missing"))?.to_owned()
            };
            out.push_str(&value);
            rest = &rest[end + 1..];
        } else {
            out.push('{');
            rest = &rest[1..];
        }
    }
    out.push_str(rest);
    Ok(out)
}

/// Same certified host, ordinary HTTPS, session credential only, max_tokens:1.
/// A fixture may override the method/path/address; its body and headers cannot
/// replace the credential or increase the completion limit.
pub fn dead_template(req: &crate::http::RequestFile, route: Option<Template>) -> Result<Template> {
    let mut t = route.unwrap_or_else(|| Template {
        method: "POST".into(), host: req.host.clone(), path: req.path.clone(),
        headers: BTreeMap::new(), body: None, credential_field: None, address: None, fixture_model: None,
    });
    if t.host != req.host { bail!("dead-check host must equal witnessed host"); }
    let body: Value = if req.method == "GET" && t.fixture_model.is_some() {
        serde_json::json!({"model":t.fixture_model})
    } else {
        serde_json::from_slice(req.body_bytes()).map_err(|_| anyhow!("dead-check needs a JSON inference body"))?
    };
    let model = body.get("model").and_then(Value::as_str)
        .ok_or_else(|| anyhow!("dead-check needs the inference model"))?;
    t.headers.clear();
    t.body = Some(serde_json::json!({"model": model, "max_tokens": 1,
        "messages": [{"role": "user", "content": "Reply pong"}]}));
    Ok(t)
}

pub async fn dead_check(t: &Template, roots: &tlsn::webpki::RootCertStore,
                        credential: &str, timeout: Duration) -> Result<(u16, Option<f64>, Option<i64>, bool, Option<String>)> {
    let (status, body) = send(t, roots, &Value::Null, false, "", timeout, Some(credential)).await?;
    Ok(probe_metadata(status, &body))
}

fn probe_metadata(status: u16, body: &Value) -> (u16, Option<f64>, Option<i64>, bool, Option<String>) {
    let completion = body.get("choices").and_then(Value::as_array).is_some_and(|v| !v.is_empty());
    let generation_id = if (200..300).contains(&status) && completion {
        body.get("id").and_then(Value::as_str).map(str::to_owned)
    } else { None };
    (status, body.pointer("/usage/cost").and_then(Value::as_f64),
        body.pointer("/error/code").and_then(Value::as_i64),
        completion, generation_id)
}

/// Returns status and, only when requested, a response parsed in memory.
/// A fresh TLS connection is used for each management request, TLS 1.2,
/// HTTP/1.1, no redirects, proxies, cookie store, or TLS key logger.
pub async fn request(t: &Template, roots: &tlsn::webpki::RootCertStore,
                     obtained: &Value, read_fields: bool, session_name: &str,
                     timeout: Duration) -> Result<(u16, Value)> {
    send(t, roots, obtained, read_fields, session_name, timeout, None).await
}

async fn send(t: &Template, roots: &tlsn::webpki::RootCertStore,
              obtained: &Value, read_fields: bool, session_name: &str,
              timeout: Duration, credential: Option<&str>) -> Result<(u16, Value)> {
    if timeout.is_zero() { bail!("management timeout must be positive"); }
    if t.host.is_empty() || !t.host.bytes().all(|b| b.is_ascii_alphanumeric() || b".-".contains(&b)) {
        bail!("invalid management host");
    }
    let path = expand(&t.path, obtained, session_name)?;
    if !path.starts_with('/') || path.starts_with("//") || path.contains(['\r', '\n', '#', '?', ' ']) {
        bail!("invalid management path");
    }
    let mut builder = reqwest::Client::builder().https_only(true).http1_only()
        .min_tls_version(reqwest::tls::Version::TLS_1_2)
        .max_tls_version(reqwest::tls::Version::TLS_1_2)
        .redirect(reqwest::redirect::Policy::none()).no_proxy()
        .tls_built_in_root_certs(false).timeout(timeout);
    for cert in &roots.roots {
        builder = builder.add_root_certificate(reqwest::Certificate::from_der(&cert.0)
            .map_err(|_| anyhow!("invalid management trust root"))?);
    }
    if let Some(addr) = t.address { builder = builder.resolve(&t.host, addr); }
    let client = builder.build().map_err(|_| anyhow!("management HTTPS client configuration failed"))?;
    let method = reqwest::Method::from_bytes(t.method.as_bytes())
        .map_err(|_| anyhow!("invalid management method"))?;
    let mut req = client.request(method, format!("https://{}{}", t.host, path));
    for (name, value) in &t.headers {
        if ["host", "connection", "content-length", "transfer-encoding"].contains(&name.to_ascii_lowercase().as_str()) {
            bail!("management framing headers are set by the HTTPS client");
        }
        req = req.header(name, expand(value, obtained, session_name)?);
    }
    if let Some(body) = &t.body {
        req = req.header("Content-Type", "application/json")
            .body(expand(&serde_json::to_string(body)?, obtained, session_name)?);
    }
    if let Some(key) = credential { req = req.bearer_auth(key); }
    let exchange = async {
        let mut response = req.header("Connection", "close").send().await?;
        let status = response.status().as_u16();
        let mut body = Vec::new();
        while let Some(chunk) = response.chunk().await? {
            // Keep even an unparsed response bounded. Never include it in errors.
            if body.len() + chunk.len() > 1 << 20 { return Ok::<_, reqwest::Error>((status, None)); }
            body.extend_from_slice(&chunk);
        }
        Ok((status, Some(body)))
    };
    let (status, body) = exchange.await.map_err(|e| {
        let refused = std::iter::successors(Some(&e as &dyn std::error::Error), |e| e.source())
            .any(|e| e.downcast_ref::<std::io::Error>().is_some_and(|e| e.kind() == std::io::ErrorKind::ConnectionRefused));
        anyhow!(if e.is_timeout() { "management request timed out" }
            else if refused { "management connection refused" }
            else if e.is_connect() { "management HTTPS connection failed" }
            else { "management HTTPS request failed" })
    })?;
    let body = body.ok_or_else(|| anyhow!("management response exceeds 1 MiB"))?;
    let fields = if read_fields && (200..300).contains(&status) {
        serde_json::from_slice(&body).map_err(|_| anyhow!("management response is not JSON"))?
    } else if credential.is_some() {
        // Probe metadata only. The caller persists cost, numeric error code,
        // completion presence and generation identifier, never the body.
        // Fixture routes need not be JSON.
        serde_json::from_slice(&body).unwrap_or(Value::Null)
    } else { Value::Null };
    Ok((status, fields))
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    #[test]
    fn provider_template_requests_and_requires_byok_limit() {
        let t: Template = serde_json::from_str(include_str!("../management/openrouter-obtain.json")).unwrap();
        assert_eq!(t.body.as_ref().unwrap()["include_byok_in_limit"], true);
        assert!(t.requires_byok_confirmation());
        let without_flag: Template = serde_json::from_value(json!({
            "method":"POST", "host":"openrouter.ai", "path":"/api/v1/keys",
            "body":{"limit":0.05}, "credential_field":"/key"})).unwrap();
        assert!(without_flag.requires_byok_confirmation());
    }

    #[test]
    fn probe_keeps_only_successful_completion_generation_id() {
        let body = json!({"id":"gen-fixture", "choices":[{}], "usage":{"cost":0.001}});
        let (status, cost, code, completion, id) = probe_metadata(200, &body);
        assert_eq!((status, cost, code, completion), (200, Some(0.001), None, true));
        assert_eq!(id.as_deref(), Some("gen-fixture"));
        assert!(probe_metadata(401, &body).4.is_none());
        assert!(probe_metadata(200, &json!({"id":"gen-fixture"})).4.is_none());
    }
}
