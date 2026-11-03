#!/usr/bin/env python3
"""Clean-room router evidence checker.

Written only from EVIDENCE-FORMAT.md (the "Router evidence interchange" text).
Python 3 standard library plus `cryptography` (used only as a secondary,
non-strict cross-check of Ed25519 signatures; the strict rule is implemented
in pure Python below because the text says a library verify call alone does
not establish it).

CLI (as specified):

  cleanroom_check.py check --evidence package.json --client-request request.http \
      --client-response response.http --trust-list trust.json

Output: one JSON object on stdout. Exit 0 only for PASS; 1 for FAIL/UNVERIFIED.

Extended in place (second clean-room pass) for the "Streaming and completion
extension" and the "Multi-connection job extension": a verified `kind:"job"`
package carries a `chain` of 3-10 entries (submit, polls, fetch); each entry
is checked as a virtual single-exchange package with the existing ordered
checks, then bound to the chain by the `job_link` and `result_digest` links.
The same four CLI inputs are used.

Every place where the text left a choice open is marked with a
`# FORMAT-GAP:` comment quoting the sentence and stating the choice made.
"""

import argparse
import hashlib
import json
import re
import sys

# ---------------------------------------------------------------------------
# Outcomes
# ---------------------------------------------------------------------------


class Fail(Exception):
    """A failing link. `link` is the failure link name; `reason` is explanatory."""

    def __init__(self, link, reason):
        super().__init__(reason)
        self.link = link
        self.reason = reason


class Unverified(Exception):
    pass


def is_int(x):
    """JSON integer: Python int but not bool (bool is an int subclass)."""
    return isinstance(x, int) and not isinstance(x, bool)


def is_uint(x, bits):
    return is_int(x) and 0 <= x < (1 << bits)


def is_str(x):
    return isinstance(x, str)


# ---------------------------------------------------------------------------
# Strict JSON
# ---------------------------------------------------------------------------

PROFILES = ("full-disclosure-fixture", "credential-hidden", "credential-sequence")
# SHA-256 of the unchanged, compiled no-CR/LF circuit files.
AUTH_CIRCUITS = (
    "431064964f5d2f0f987d2f1a4d38e1c946065a0de9f9e2fbff2a09082a1edd1c",
    "504c3254ea2da2cbbce48ca37953cb591710ad1b4a494ac5cb5858050d77ad3d",
    "a59c1d2d199d0ff0a660314fd08df73b417e9b1ebee23be7d30675474ff79c57",
    "f475261ee6fba85d17dddbd4d183fcc925ff791ceb3c6d969c078214af7dd342",
)

INT_MIN = -(1 << 63)
INT_MAX = (1 << 64) - 1


class JsonError(Exception):
    pass


def _parse_int(literal):
    # "Negative zero (`-0`) is also rejected."
    if literal == "-0":
        raise JsonError("negative zero")
    v = int(literal)
    # "Numbers must fit an integer in [-2^63, 2^64-1]"
    if v < INT_MIN or v > INT_MAX:
        raise JsonError("integer out of range")
    return v


def _parse_float(literal):
    # "any number containing `.`, `e` or `E`" is rejected
    raise JsonError("non-integer number: %s" % literal)


def _parse_constant(literal):
    # NaN / Infinity / -Infinity
    raise JsonError("non-finite constant: %s" % literal)


def _check_surrogates(x):
    # "Reject ... unpaired Unicode surrogates". Python's json decoder turns a
    # lone `\udXXX` escape into a lone surrogate code point; find them here.
    if isinstance(x, str):
        for ch in x:
            if 0xD800 <= ord(ch) <= 0xDFFF:
                raise JsonError("unpaired surrogate in string")
    elif isinstance(x, dict):
        for k, v in x.items():
            _check_surrogates(k)
            _check_surrogates(v)
    elif isinstance(x, list):
        for v in x:
            _check_surrogates(v)


def strict_json_loads(data):
    """Parse bytes as the strict JSON subset. Raises JsonError."""
    try:
        text = data.decode("utf-8")  # strict: rejects invalid UTF-8 and encoded surrogates
    except UnicodeDecodeError as e:
        raise JsonError("not UTF-8: %s" % e)
    try:
        # Duplicate member names: Python's dict construction keeps the last
        # value, matching "Duplicate member names resolve to the last value".
        value = json.loads(
            text,
            parse_int=_parse_int,
            parse_float=_parse_float,
            parse_constant=_parse_constant,
        )
    except JsonError:
        raise
    except (ValueError, RecursionError) as e:
        raise JsonError("invalid JSON: %s" % e)
    _check_surrogates(value)
    return value


def canonical(x):
    """C(x): the canonical encoding described in the text."""
    # The text states Python's json.dumps with these options gives C for the
    # supported subset. Our strict loader guarantees the subset (ints only,
    # no surrogates), so this is exact.
    return json.dumps(x, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_hex(b):
    return hashlib.sha256(b).hexdigest()


# ---------------------------------------------------------------------------
# Hex helpers
# ---------------------------------------------------------------------------

HEX_RE = re.compile(r"[0-9a-fA-F]*", re.ASCII)


def decode_hex(s, nbytes):
    """Decode a hex string in any case to exactly nbytes. Returns bytes or None."""
    if not is_str(s):
        return None
    if len(s) != 2 * nbytes or HEX_RE.fullmatch(s) is None:
        return None
    return bytes.fromhex(s)


# ---------------------------------------------------------------------------
# Strict Ed25519 (pure Python, RFC 8032 arithmetic + verify_strict rules)
# ---------------------------------------------------------------------------

P = (1 << 255) - 19
L_ORDER = (1 << 252) + 27742317777372353535851937790883648493


def _inv(x):
    return pow(x, P - 2, P)


D_CONST = (-121665 * _inv(121666)) % P
SQRT_M1 = pow(2, (P - 1) // 4, P)

# Points in extended coordinates (X, Y, Z, T) with x = X/Z, y = Y/Z, xy = T/Z.
IDENTITY = (0, 1, 1, 0)


def _pt_add(p1, p2):
    x1, y1, z1, t1 = p1
    x2, y2, z2, t2 = p2
    a = ((y1 - x1) * (y2 - x2)) % P
    b = ((y1 + x1) * (y2 + x2)) % P
    c = (2 * t1 * t2 * D_CONST) % P
    d = (2 * z1 * z2) % P
    e = b - a
    f = d - c
    g = d + c
    h = b + a
    return ((e * f) % P, (g * h) % P, (f * g) % P, (e * h) % P)


def _pt_mul(k, pt):
    acc = IDENTITY
    while k > 0:
        if k & 1:
            acc = _pt_add(acc, pt)
        pt = _pt_add(pt, pt)
        k >>= 1
    return acc


def _pt_neg(pt):
    x, y, z, t = pt
    return ((-x) % P, y, z, (-t) % P)


def _pt_is_identity(pt):
    x, y, z, t = pt
    # identity is x = 0, y = 1  (as projective: X == 0 and Y == Z)
    return x % P == 0 and (y - z) % P == 0


def _pt_encode(pt):
    x, y, z, t = pt
    zi = _inv(z)
    x = (x * zi) % P
    y = (y * zi) % P
    enc = bytearray(y.to_bytes(32, "little"))
    if x & 1:
        enc[31] |= 0x80
    return bytes(enc)


def _pt_decode(b):
    """Edwards25519 field decoder.

    FORMAT-GAP: "A is decoded with the Edwards25519 field decoder; no additional
    re-encoding check of A is required." RFC 8032 rejects y >= p outright,
    while a "field decoder" that loads 255 bits (as ed25519-dalek does) reduces
    y modulo p instead. Choice: reduce modulo p (dalek behaviour) for both A
    and R. For R this cannot change the outcome because the computed R is
    compared against the signature bytes; for A it only matters for a
    noncanonical key encoding, which also cannot match a trust-list key here.
    """
    if len(b) != 32:
        return None
    y = int.from_bytes(b, "little")
    sign = (y >> 255) & 1
    y &= (1 << 255) - 1
    y %= P
    y2 = (y * y) % P
    u = (y2 - 1) % P
    v = (D_CONST * y2 + 1) % P
    x = (u * pow(v, 3, P) * pow((u * pow(v, 7, P)) % P, (P - 5) // 8, P)) % P
    vx2 = (v * x * x) % P
    if vx2 == u:
        pass
    elif vx2 == (-u) % P:
        x = (x * SQRT_M1) % P
    else:
        return None
    if x == 0 and sign == 1:
        return None  # RFC 8032 5.1.3 step 4
    if (x & 1) != sign:
        x = (-x) % P
    return (x, y, 1, (x * y) % P)


_BASE_Y = (4 * _inv(5)) % P
_BASE = _pt_decode(_BASE_Y.to_bytes(32, "little"))
assert _BASE is not None


def ed25519_verify_strict(pub_bytes, sig_bytes, msg):
    """Return (ok: bool, reason: str)."""
    if len(pub_bytes) != 32 or len(sig_bytes) != 64:
        return False, "bad key or signature length"
    r_bytes = sig_bytes[:32]
    s = int.from_bytes(sig_bytes[32:], "little")
    if s >= L_ORDER:
        return False, "S >= L"
    a = _pt_decode(pub_bytes)
    if a is None:
        return False, "public key does not decode as an Edwards25519 point"
    r = _pt_decode(r_bytes)
    if r is None:
        return False, "R does not decode as an Edwards25519 point"
    if _pt_is_identity(_pt_mul(8, a)):
        return False, "public key is a small-order point"
    if _pt_is_identity(_pt_mul(8, r)):
        return False, "R is a small-order point"
    k = int.from_bytes(hashlib.sha512(r_bytes + pub_bytes + msg).digest(), "little") % L_ORDER
    computed = _pt_add(_pt_mul(s, _BASE), _pt_neg(_pt_mul(k, a)))
    if _pt_encode(computed) != r_bytes:
        return False, "signature equation does not hold"
    # Secondary, non-strict cross-check with the library (a superset acceptor).
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        from cryptography.exceptions import InvalidSignature

        try:
            Ed25519PublicKey.from_public_bytes(pub_bytes).verify(sig_bytes, msg)
        except InvalidSignature:
            return False, "library cross-check rejected the signature"
        except ValueError:
            return False, "library cross-check rejected the key"
    except ImportError:
        pass
    return True, "ok"


def verify_signed_object(obj, pub_hex, sig_value):
    """Verify sig over C(obj minus top-level sig). Returns (ok, reason)."""
    pub = decode_hex(pub_hex, 32)
    if pub is None:
        return False, "public key is not 64 hex characters"
    sig = decode_hex(sig_value, 64)
    if sig is None:
        return False, "signature is not 128 hex characters"
    body = {k: v for k, v in obj.items() if k != "sig"}
    return ed25519_verify_strict(pub, sig, canonical(body))


# ---------------------------------------------------------------------------
# RFC3339 verified_at
# ---------------------------------------------------------------------------

RFC3339_RE = re.compile(
    r"([0-9]{4})-([0-9]{2})-([0-9]{2})T([0-9]{2}):([0-9]{2}):([0-9]{2})"
    r"(\.[0-9]+)?(Z|z|[+-][0-9]{2}:[0-9]{2})",
    re.ASCII,
)


def _days_in_month(y, m):
    if m in (1, 3, 5, 7, 8, 10, 12):
        return 31
    if m in (4, 6, 9, 11):
        return 30
    leap = (y % 4 == 0 and y % 100 != 0) or (y % 400 == 0)
    return 29 if leap else 28


def valid_rfc3339(s):
    if not is_str(s) or not s.isascii():
        return False
    m = RFC3339_RE.fullmatch(s)
    if m is None:
        return False
    y, mo, d, hh, mm, ss = (int(m.group(i)) for i in range(1, 7))
    if not (1 <= mo <= 12):
        return False
    if not (1 <= d <= _days_in_month(y, mo)):
        return False
    if hh > 23 or mm > 59 or ss > 60:
        return False
    off = m.group(8)
    if off not in ("Z", "z"):
        if int(off[1:3]) > 23 or int(off[4:6]) > 59:
            return False
    # FORMAT-GAP: "Seconds may be 00–60" — a value of 60 is accepted at any
    # time, not only at a real leap-second instant. Choice: accept any 60.
    # FORMAT-GAP: year 0000 is matched by "four-digit year"; RFC 3339 itself
    # allows 0000. Choice: accept year 0000.
    return True


# ---------------------------------------------------------------------------
# HTTP/1.x message parsing
# ---------------------------------------------------------------------------

TOKEN_RE = re.compile(rb"[!#$%&'*+\-.^_`|~0-9A-Za-z]+")
MAX_HEADERS = 64


class HeadError(Exception):
    """Structural head error (start line, header lines, terminator)."""


class FramingError(Exception):
    """Body framing or consulted-header error."""


def split_head(data):
    """Return (start_line, header_lines, rest). Raises HeadError."""
    pos = 0
    lines = []
    started = False
    while True:
        idx = data.find(b"\n", pos)
        if idx < 0:
            raise HeadError("missing head terminator")
        line = data[pos:idx]
        if line.endswith(b"\r"):
            line = line[:-1]
        if b"\r" in line:
            raise HeadError("bare CR in head")
        pos = idx + 1
        if line == b"":
            if not started:
                continue  # leading empty lines before the start line
            break
        started = True
        lines.append(line)
    return lines[0], lines[1:], data[pos:]


def parse_header_lines(header_lines):
    """Return list of (lowercase_name: str, value: str) in wire order."""
    if len(header_lines) > MAX_HEADERS:
        raise HeadError("more than %d headers" % MAX_HEADERS)
    headers = []
    for line in header_lines:
        if line[:1] in (b" ", b"\t"):
            raise HeadError("obsolete line folding")
        idx = line.find(b":")
        if idx < 0:
            raise HeadError("header line without colon")
        name = line[:idx]
        if not name or TOKEN_RE.fullmatch(name) is None:
            # covers empty names, whitespace before ':' and non-token bytes
            raise HeadError("invalid header name")
        value = line[idx + 1 :].strip(b" \t")
        for b in value:
            # FORMAT-GAP: "control bytes other than HTAB in values" are
            # rejected. DEL (0x7F) is a control byte in RFC 9110's CTL set
            # but not in the 0x00–0x1F range; choice: reject 0x7F as well.
            if (b < 0x20 and b != 0x09) or b == 0x7F:
                raise HeadError("control byte in header value")
        try:
            value_s = value.decode("utf-8")
        except UnicodeDecodeError:
            raise HeadError("header value is not UTF-8")
        headers.append((name.decode("ascii").lower(), value_s))
    return headers


def header_values(headers, name):
    return [v for n, v in headers if n == name]


def parse_request_line(line):
    """Return (method: bytes, target: bytes). Raises HeadError."""
    # FORMAT-GAP: "Keep the method and request target literally from the
    # request line." The text does not say how strictly the request line is
    # tokenised. Choice: exactly three parts separated by single SP, method a
    # nonempty token, target nonempty, version exactly HTTP/1.0 or HTTP/1.1.
    parts = line.split(b" ")
    if len(parts) != 3:
        raise HeadError("request line must be METHOD SP target SP version")
    method, target, version = parts
    if TOKEN_RE.fullmatch(method) is None:
        raise HeadError("method is not a token")
    if not target:
        raise HeadError("empty request target")
    if version not in (b"HTTP/1.0", b"HTTP/1.1"):
        raise HeadError("unsupported HTTP version")
    return method, target


def parse_status_line(line):
    """Return status (int). Raises HeadError."""
    if line[:8] not in (b"HTTP/1.0", b"HTTP/1.1"):
        raise HeadError("unsupported HTTP version")
    if line[8:9] != b" ":
        raise HeadError("status line missing SP after version")
    code = line[9:12]
    if len(code) != 3 or not all(0x30 <= b <= 0x39 for b in code):
        raise HeadError("status must be exactly three ASCII digits")
    # FORMAT-GAP: the text does not say whether the SP before the reason
    # phrase is required when the reason is empty ("HTTP/1.1 200" vs
    # "HTTP/1.1 200 "). Choice: accept either; anything else directly after
    # the three digits (e.g. a fourth digit) is a status-width error.
    if len(line) > 12 and line[12:13] != b" ":
        raise HeadError("status must be exactly three ASCII digits")
    return int(code.decode("ascii"))


DIGITS_RE = re.compile(rb"[0-9]+")


def parse_content_length(value_s):
    v = value_s.encode("utf-8")
    if DIGITS_RE.fullmatch(v) is None:
        raise FramingError("Content-Length is not one or more ASCII digits")
    return int(v.decode("ascii"))


CHUNK_SIZE_RE = re.compile(r"\+?[0-9A-Fa-f]+", re.ASCII)


def parse_chunked(data):
    """Return (body_bytes, rest). Raises FramingError."""
    # FORMAT-GAP: "parse a CRLF-terminated hex size" and "consume trailer
    # lines through the next empty line". Only start/header lines are said
    # to accept bare LF; choice: chunk-size lines, chunk-data terminators and
    # trailer lines require CRLF.
    pos = 0
    out = bytearray()
    while True:
        idx = data.find(b"\r\n", pos)
        if idx < 0:
            raise FramingError("chunk size line not CRLF-terminated")
        size_line = data[pos:idx]
        semi = size_line.find(b";")
        size_text = size_line if semi < 0 else size_line[:semi]
        try:
            size_text = size_text.decode("utf-8").strip()
        except UnicodeDecodeError:
            raise FramingError("chunk size is not UTF-8")
        if CHUNK_SIZE_RE.fullmatch(size_text) is None:
            raise FramingError("invalid chunk size")
        size = int(size_text.lstrip("+"), 16)
        pos = idx + 2
        if size == 0:
            break
        chunk = data[pos : pos + size]
        if len(chunk) != size:
            raise FramingError("truncated chunk")
        pos += size
        if data[pos : pos + 2] != b"\r\n":
            raise FramingError("chunk data not followed by CRLF")
        pos += 2
        out += chunk
    while True:
        idx = data.find(b"\r\n", pos)
        if idx < 0:
            raise FramingError("trailer section not terminated")
        line = data[pos:idx]
        pos = idx + 2
        if line == b"":
            break
    return bytes(out), data[pos:]


def parse_request(data):
    """Parse the retained request. Returns (method, target, headers, body, rest).

    Raises HeadError or FramingError (both belong to request_match).
    """
    start, header_lines, rest = split_head(data)
    method, target = parse_request_line(start)
    headers = parse_header_lines(header_lines)
    cl = header_values(headers, "content-length")
    te = header_values(headers, "transfer-encoding")
    if len(cl) > 1:
        raise FramingError("duplicate Content-Length")
    if len(te) > 1:
        raise FramingError("duplicate Transfer-Encoding")
    if cl and te:
        raise FramingError("both Content-Length and Transfer-Encoding")
    for ev in header_values(headers, "expect"):
        # FORMAT-GAP: "Reject unsupported Expect values (only case-insensitive
        # 100-continue)". Choice: every Expect header present must equal
        # 100-continue case-insensitively (after ordinary value trimming).
        if ev.lower() != "100-continue":
            raise FramingError("unsupported Expect value")
    if te:
        if te[0].lower() != "chunked":
            raise FramingError("Transfer-Encoding must be chunked")
        body, rest = parse_chunked(rest)
    elif cl:
        n = parse_content_length(cl[0])
        body = rest[:n]
        if len(body) != n:
            raise FramingError("body shorter than Content-Length")
        rest = rest[n:]
    else:
        body = b""
    return method, target, headers, body, rest


def skip_informational(data):
    """Step 1: remove leading `HTTP/1.1 100 ` heads, each through its first CRLF CRLF."""
    while data.startswith(b"HTTP/1.1 100 "):
        idx = data.find(b"\r\n\r\n")
        if idx < 0:
            break  # missing terminator: leave the head to fail later parsing
        data = data[idx + 4 :]
    return data


def parse_response_head(data):
    """Parse the final response head. Returns (status, headers, rest). Raises HeadError."""
    start, header_lines, rest = split_head(data)
    status = parse_status_line(start)
    headers = parse_header_lines(header_lines)
    return status, headers, rest


def frame_response_body(status, headers, rest):
    """Return (content_type_or_None, body, trailing). Raises FramingError."""
    te = header_values(headers, "transfer-encoding")
    cl = header_values(headers, "content-length")
    ct = header_values(headers, "content-type")
    if len(te) > 1:
        raise FramingError("duplicate Transfer-Encoding")
    if te:
        if te[0].lower() != "chunked":
            raise FramingError("Transfer-Encoding must be chunked")
        body, trailing = parse_chunked(rest)
    elif status in (204, 304):
        body, trailing = b"", rest
    elif cl:
        if len(cl) > 1:
            raise FramingError("duplicate Content-Length")
        n = parse_content_length(cl[0])
        body = rest[:n]
        if len(body) != n:
            raise FramingError("body shorter than Content-Length")
        trailing = rest[n:]
    else:
        body, trailing = rest, b""
    if len(ct) > 1:
        raise FramingError("duplicate Content-Type")
    content_type = ct[0] if ct else None
    return content_type, body, trailing


def forwarded_digest(headers):
    pairs = [[n, v] for n, v in headers if n == "content-type" or n.startswith("x-client-")]
    return sha256_hex(canonical(pairs))


# ---------------------------------------------------------------------------
# Package decoding (step 4: inclusion)
# ---------------------------------------------------------------------------


def incl(reason):
    return Fail("inclusion", reason)


def require_str(obj, name, where):
    v = obj.get(name)
    if not is_str(v):
        raise incl("%s.%s must be a string" % (where, name))
    return v


def require_uint(obj, name, where, bits=64):
    v = obj.get(name)
    if not is_uint(v, bits):
        raise incl("%s.%s must be an unsigned %d-bit integer" % (where, name, bits))
    return v


def decode_record(record):
    """Type-check the record. Returns a dict of decoded facts for later links."""
    if not isinstance(record, dict):
        raise incl("receipt.record must be an object")
    facts = {}
    require_str(record, "session_id", "record")
    for name in ("operator_pub", "operator_statement_sha256"):
        v = record.get(name)
        if v is not None and not is_str(v):
            raise incl("record.%s must be a string or null" % name)
    require_uint(record, "n", "record")
    require_str(record, "job_id", "record")
    outcome = require_str(record, "outcome", "record")
    if outcome != "verified":
        raise incl("record.outcome must be 'verified'")
    require_str(record, "salt", "record")

    req = record.get("request")
    if not isinstance(req, dict):
        raise incl("record.request must be an object")
    for name in ("method", "host", "path", "body_sha256", "forwarded_headers_sha256"):
        require_str(req, name, "record.request")
    require_uint(req, "body_bytes", "record.request")
    withheld = req.get("withheld")
    facts["withheld_object"] = False
    if withheld is not None:
        if not isinstance(withheld, dict):
            raise incl("record.request.withheld must be null or an object")
        # Type errors fail inclusion; profile/proof policy is checked at session.
        if not (is_uint(withheld.get("start"), 64) and is_uint(withheld.get("end"), 64)
                and is_str(withheld.get("no_cr_lf")) and is_str(withheld.get("header"))):
            raise incl("record.request.withheld object is ill-typed")
        facts["withheld_object"] = True

    resp = record.get("response")
    if not isinstance(resp, dict):
        raise incl("record.response must be an object")
    require_uint(resp, "status", "record.response", bits=16)
    if "content_type" not in resp:
        raise incl("record.response.content_type is absent")
    ct = resp["content_type"]
    if ct is not None and not is_str(ct):
        raise incl("record.response.content_type must be a string or null")
    require_str(resp, "body_sha256", "record.response")
    require_uint(resp, "body_bytes", "record.response")
    require_str(resp, "transfer", "record.response")
    if "images" in resp:
        images = resp["images"]
        if not isinstance(images, list):
            raise incl("record.response.images must be an array")
        for img in images:
            if not isinstance(img, dict):
                raise incl("record.response.images element must be an object")
            require_str(img, "media_type", "record.response.images[]")
            require_str(img, "sha256", "record.response.images[]")
            require_uint(img, "bytes", "record.response.images[]")
    return facts


def decode_verdict(verdict):
    if not isinstance(verdict, dict):
        raise incl("receipt.verdict must be an object")
    facts = {}
    v = verdict.get("v")
    if not is_uint(v, 32):
        raise incl("verdict.v must be an unsigned 32-bit integer")
    if v != 5:
        raise incl("verdict.v must be 5")
    for name in ("session_id", "mode", "server_name", "root", "verified_at", "verifier_pub"):
        require_str(verdict, name, "verdict")
    require_uint(verdict, "exchanges", "verdict")
    limits = verdict.get("limits")
    if not isinstance(limits, dict):
        raise incl("verdict.limits must be an object")
    require_uint(limits, "max_sent", "verdict.limits")
    require_uint(limits, "max_recv", "verdict.limits")
    profile = verdict.get("profile")
    if not is_str(profile) or profile not in PROFILES:
        raise incl("verdict.profile must name one explicit witnessing profile")
    facts["profile"] = profile
    if "sig" in verdict:
        if not is_str(verdict["sig"]):
            raise incl("verdict.sig must be a string")
        facts["sig"] = verdict["sig"]
    else:
        facts["sig"] = None
    return facts


def merkle_root(leaf_hex, index, count, path):
    """Compute the root per the text. Raises Fail('inclusion')."""
    if not (0 <= index < count):
        raise incl("exchange index out of range")
    h = bytes.fromhex(leaf_hex)
    siblings = []
    for s in path:
        b = decode_hex(s, 32)
        if b is None:
            raise incl("Merkle sibling is not 64 hex characters")
        siblings.append(b)
    i, c, used = index, count, 0
    while c > 1:
        if (i ^ 1) < c:
            if used >= len(siblings):
                raise incl("Merkle path too short")
            s = siblings[used]
            used += 1
            if i % 2 == 0:
                h = hashlib.sha256(b"\x01" + h + s).digest()
            else:
                h = hashlib.sha256(b"\x01" + s + h).digest()
        i //= 2
        c = (c + 1) // 2
    if used != len(siblings):
        raise incl("Merkle path has unused siblings")
    return h.hex()


# ---------------------------------------------------------------------------
# Trust list (read at step 5)
# ---------------------------------------------------------------------------


def load_trust_list(path):
    def bad(reason):
        return Fail("witness_signature", "trust list: " + reason)

    try:
        with open(path, "rb") as f:
            data = f.read()
    except OSError as e:
        raise bad("cannot read: %s" % e)
    try:
        trust = strict_json_loads(data)
    except JsonError as e:
        raise bad("invalid JSON: %s" % e)
    if not isinstance(trust, dict):
        raise bad("top level must be an object")
    if set(trust.keys()) != {"v", "witnesses", "operators", "server_name", "path"}:
        raise bad("exactly v, witnesses, operators, server_name and path are required")
    if not (is_int(trust["v"]) and trust["v"] == 1):
        raise bad("v must be 1")
    witnesses = trust["witnesses"]
    if not isinstance(witnesses, list):
        raise bad("witnesses must be an array")
    for w in witnesses:
        if not isinstance(w, dict) or set(w.keys()) != {"label", "public_key", "profiles"}:
            raise bad("each witness has exactly label, public_key and profiles")
        if not (is_str(w["label"]) and is_str(w["public_key"])):
            raise bad("witness label and public_key must be strings")
        if not isinstance(w["profiles"], list) or not all(is_str(p) and p in PROFILES for p in w["profiles"]):
            raise bad("witness profiles must be an array of supported profile names")
    operators = trust["operators"]
    if not isinstance(operators, list) or not all(is_str(o) for o in operators):
        raise bad("operators must be an array of strings")
    if not is_str(trust["server_name"]) or not is_str(trust["path"]):
        raise bad("server_name and path must be strings")
    return trust


# ---------------------------------------------------------------------------
# The ordered checks (single exchange)
# ---------------------------------------------------------------------------
#
# The single-exchange checks are written as a function over an in-memory
# package object plus loaders for the request/response bytes, so that the job
# chain can run "**all** existing ordered single-exchange checks" against a
# virtual package and hex-decoded HTTP representations.


def file_loader(path, link, what):
    """A loader that reads a client file; a read error belongs to `link`."""

    def load():
        try:
            with open(path, "rb") as f:
                return f.read()
        except OSError as e:
            raise Fail(link, "cannot read %s: %s" % (what, e))

    return load


def bytes_loader(data):
    def load():
        return data

    return load


def load_package(evidence_path):
    """Step 1 (first half): read the package JSON and require v == 1."""
    try:
        with open(evidence_path, "rb") as f:
            pkg_bytes = f.read()
    except OSError as e:
        raise Fail("evidence", "cannot read package: %s" % e)
    try:
        pkg = strict_json_loads(pkg_bytes)
    except JsonError as e:
        raise Fail("evidence", "package is not valid JSON: %s" % e)
    if not isinstance(pkg, dict):
        raise Fail("evidence", "package must be a JSON object")
    if not (is_int(pkg.get("v")) and pkg["v"] == 1):
        raise Fail("evidence", "package v must be 1")
    return pkg


def single_exchange_checks(pkg, request_loader, response_loader, trust_path, path_override, ctx):
    """Steps 1 (response read) through 13 for one exchange.

    `pkg` is an already-parsed v1 package object (step 1's package read and
    `v == 1` check have been done by the caller). `ctx['label']` receives the
    selected witness label as soon as one is selected, so a FAIL after that
    point reports it. `path_override`, when not None, replaces trust.path for
    the destination check ("use the signed exchange's request.path as the
    temporary destination path").

    Raises Fail or Unverified. Returns a dict of facts used by the job chain.
    """
    ctx["profile"] = None
    ctx["label"] = None
    # Each exchange reports only its own selected witness, including in chains.
    # 1. evidence (second half) ------------------------------------------
    response_bytes = response_loader()
    response_final = skip_informational(response_bytes)

    # 2. receipt_match ---------------------------------------------------
    try:
        status, resp_headers, resp_rest = parse_response_head(response_final)
    except HeadError as e:
        raise Fail("receipt_match", "response head: %s" % e)
    receipts = header_values(resp_headers, "x-witness-receipt")
    if len(receipts) != 1:
        raise Fail("receipt_match", "response must carry exactly one X-Witness-Receipt header")
    client_receipt_id = receipts[0]
    outer_id = pkg.get("receipt_id")
    if not is_str(outer_id) or outer_id != client_receipt_id:
        raise Fail("receipt_match", "package receipt_id does not equal the response receipt header")

    # 3. evidence (state) -------------------------------------------------
    state = pkg.get("state")
    if state == "unverified" and "receipt" not in pkg:
        # FORMAT-GAP: "an honest unverified job has no outer `receipt` or
        # `chain`" but the early-UNVERIFIED rule itself names only the
        # `receipt` member ("`receipt:null` is present and does not
        # qualify"). Choice: an unverified package with `receipt` absent is
        # UNVERIFIED even if a `chain` or `witnessed_receipt` member is
        # present; those extensions are not consulted.
        raise Unverified()
    if state == "pending":
        # FORMAT-GAP: "If state is `pending`, return FAIL(**evidence_pending**)."
        # The step is headed **evidence** and `evidence_pending` appears
        # nowhere else as a link, so this was first read as a reason under
        # link `evidence`. Changed AFTER opening the sealed results: FAIL's
        # only named slot is `link`, and the bold token is styled like the
        # other link names, so the link is `evidence_pending`.
        # (The current text now lists `evidence_pending` as its own link.)
        raise Fail("evidence_pending", "operator evidence is still pending")
    if state != "verified":
        raise Fail("evidence", "package state is not verified")

    # 4. inclusion ---------------------------------------------------------
    receipt = pkg.get("receipt")
    if not isinstance(receipt, dict):
        raise incl("receipt must be an object")
    if not (is_int(receipt.get("v")) and receipt["v"] == 1):
        raise incl("receipt.v must be 1")
    record = receipt.get("record")
    rec_facts = decode_record(record)
    verdict = receipt.get("verdict")
    ver_facts = decode_verdict(verdict)
    path = receipt.get("path")
    if not isinstance(path, list):
        raise incl("receipt.path must be an array")
    leaf = sha256_hex(canonical(record))
    root = merkle_root(leaf, record["n"] - 1, verdict["exchanges"], path)
    if root != verdict["root"]:
        raise incl("computed Merkle root does not equal verdict.root")

    # 5. witness_signature -------------------------------------------------
    if ver_facts["sig"] is None:
        raise Fail("witness_signature", "verdict.sig is absent")
    ok, why = verify_signed_object(verdict, verdict["verifier_pub"], ver_facts["sig"])
    if not ok:
        raise Fail("witness_signature", "verdict signature invalid: %s" % why)
    trust = load_trust_list(trust_path)
    if path_override is not None:
        trust = dict(trust)
        trust["path"] = path_override
    wk = pkg.get("witness_key_id")
    if not is_str(wk) or wk != verdict["verifier_pub"]:
        raise Fail("witness_signature", "witness_key_id does not equal verdict.verifier_pub")
    matches = [w for w in trust["witnesses"] if w["public_key"] == wk]
    if not matches:
        raise Fail("witness_signature", "witness key is not in the trust list")
    ctx["label"] = matches[-1]["label"]
    ctx["profile"] = ver_facts["profile"]

    # 6. session -----------------------------------------------------------
    if not valid_rfc3339(verdict["verified_at"]):
        raise Fail("session", "verdict.verified_at is not a valid RFC3339 date-time")
    if record["session_id"] != verdict["session_id"]:
        raise Fail("session", "record.session_id does not equal verdict.session_id")
    if ver_facts["profile"] not in matches[-1]["profiles"]:
        raise Fail("session", "witness profile is not accepted by the trust list")
    if ver_facts["profile"] == "credential-hidden":
        w = record["request"].get("withheld")
        if not rec_facts["withheld_object"] or w["start"] >= w["end"] or w["no_cr_lf"] not in AUTH_CIRCUITS or w["header"] not in ("authorization", "x-api-key"):
            raise Fail("session", "credential-hidden requires the known credential header proof")
    elif rec_facts["withheld_object"]:
        raise Fail("session", "full disclosure profile forbids withheld ranges")

    # 7. receipt_match -----------------------------------------------------
    if record["job_id"] != client_receipt_id:
        raise Fail("receipt_match", "record.job_id does not equal the client receipt id")

    # 8. operator_identity -------------------------------------------------
    stmt = pkg.get("operator_statement")
    if not isinstance(stmt, dict):
        raise Fail("operator_identity", "operator_statement is absent or not an object")
    # FORMAT-GAP: the decoding table does not list operator_statement.sig
    # or operator_statement.operator_pub. "An absent/non-object outer
    # operator_statement fails operator_identity." Choice: every defect of
    # the statement (missing/ill-typed sig or key, bad hex) fails
    # operator_identity, since the whole statement is checked at step 8.
    if "sig" not in stmt:
        raise Fail("operator_identity", "operator_statement.sig is absent")
    if not is_str(stmt["sig"]) or not is_str(stmt.get("operator_pub")):
        raise Fail("operator_identity", "operator_statement sig/operator_pub must be strings")
    ok, why = verify_signed_object(stmt, stmt["operator_pub"], stmt["sig"])
    if not ok:
        raise Fail("operator_identity", "operator statement signature invalid: %s" % why)
    rec_op = record.get("operator_pub")
    if rec_op is None:
        raise Fail("operator_identity", "record.operator_pub is absent")
    if rec_op != stmt["operator_pub"]:
        raise Fail("operator_identity", "record.operator_pub differs from statement.operator_pub")
    if rec_op not in trust["operators"]:
        raise Fail("operator_identity", "operator key is not in trust.operators")
    rec_hash = record.get("operator_statement_sha256")
    if rec_hash is None:
        raise Fail("operator_identity", "record.operator_statement_sha256 is absent")
    if sha256_hex(canonical(stmt)) != rec_hash:
        raise Fail("operator_identity", "record.operator_statement_sha256 does not match H(C(statement))")
    req = record["request"]
    comparisons = [
        ("session_id", record["session_id"]),
        ("receipt_id", record["job_id"]),
        ("method", req["method"]),
        ("host", req["host"]),
        ("path", req["path"]),
        ("body_sha256", req["body_sha256"]),
        ("body_bytes", req["body_bytes"]),
        ("forwarded_headers_sha256", req["forwarded_headers_sha256"]),
    ]
    for name, rec_value in comparisons:
        sv = stmt.get(name)
        # type-aware equality: True == 1 in Python, so compare types too
        if type(sv) is not type(rec_value) or sv != rec_value:
            raise Fail("operator_identity", "statement.%s does not equal the record" % name)

    # 9. destination ------------------------------------------------------
    if verdict["server_name"] != trust["server_name"]:
        raise Fail("destination", "verdict.server_name does not equal trust.server_name")
    if req["host"] != trust["server_name"]:
        raise Fail("destination", "record.request.host does not equal trust.server_name")
    if req["path"] != trust["path"]:
        raise Fail("destination", "record.request.path does not equal trust.path")

    # 10. request_match ---------------------------------------------------
    request_bytes = request_loader()
    try:
        method, target, req_headers, req_body, req_rest = parse_request(request_bytes)
    except (HeadError, FramingError) as e:
        raise Fail("request_match", "request: %s" % e)
    if req_rest:
        raise Fail("request_match", "trailing bytes after the request message")
    if method != req["method"].encode("utf-8"):
        raise Fail("request_match", "request method differs from record")
    if target != req["path"].encode("utf-8"):
        raise Fail("request_match", "request target differs from record.request.path")
    if len(req_body) != req["body_bytes"]:
        raise Fail("request_match", "request body length differs from record")
    if sha256_hex(req_body) != req["body_sha256"]:
        raise Fail("request_match", "request body hash differs from record")

    # 11. forwarded_headers -----------------------------------------------
    if forwarded_digest(req_headers) != req["forwarded_headers_sha256"]:
        raise Fail("forwarded_headers", "forwarded header digest differs from record")

    # 12. response_delivery -----------------------------------------------
    try:
        content_type, resp_body, trailing = frame_response_body(status, resp_headers, resp_rest)
    except FramingError as e:
        raise Fail("response_delivery", "response: %s" % e)
    if trailing:
        raise Fail("response_delivery", "trailing bytes after the response message")
    rr = record["response"]
    if status != rr["status"]:
        raise Fail("response_delivery", "response status differs from record")
    if content_type != rr["content_type"]:
        raise Fail("response_delivery", "response Content-Type differs from record")
    if len(resp_body) != rr["body_bytes"]:
        raise Fail("response_delivery", "response body length differs from record")
    if sha256_hex(resp_body) != rr["body_sha256"]:
        raise Fail("response_delivery", "response body hash differs from record")

    # 13. receipt_match ---------------------------------------------------
    receipts = header_values(resp_headers, "x-witness-receipt")
    if len(receipts) != 1 or receipts[0] != client_receipt_id:
        raise Fail("receipt_match", "final response receipt header mismatch")

    return {
        "record": record,
        "verdict": verdict,
        "status": status,
        "content_type": content_type,
        "response_body": resp_body,
        "request_method": method,
        "request_target": target,
        "request_body": req_body,
    }


# ---------------------------------------------------------------------------
# Streaming and completion extension
# ---------------------------------------------------------------------------
#
# Nothing in this extension adds a check. "The checker's existing response
# framing parser removes the client-side chunk coding and compares the entire
# resulting body, its length, status and Content-Type against the witness
# record." The outer `delivery` object "is **not consulted by `check`**", and
# an unverified package's `witnessed_receipt` extension is "for inspection
# only" (the early-UNVERIFIED rule looks only at `receipt`).
#
# FORMAT-GAP: "A request asks for streaming when its retained JSON body has a
# top-level `stream` member whose value is JSON boolean `true` (last duplicate
# wins)." No check in the text consumes this classification: the body is
# authenticated by the existing request-body hash and no link depends on
# whether the request asked for streaming. Choice: the checker does not parse
# the request body at all; a streamed and a non-streamed exchange are checked
# identically.


# ---------------------------------------------------------------------------
# Multi-connection job extension
# ---------------------------------------------------------------------------

JOB_LINKS = ("job_link", "result_digest")
JOB_ID_RE = re.compile(r"[A-Za-z0-9_\-]{1,128}", re.ASCII)
CHAIN_MIN, CHAIN_MAX = 3, 10


def is_job_package(pkg):
    """Decide whether the chain checks apply.

    FORMAT-GAP: "A verified job package has `v:1`, `kind:"job"`,
    `state:"verified"`, one `receipt_id`, and a `chain` array instead of the
    outer `receipt`...". The text does not say which member *selects* the
    chain checks. Choice: `kind == "job"` selects them, so a verified
    `kind:"job"` package without a chain fails `evidence` at chain step 1
    ("Dropping a chain cannot produce PASS"), while a package carrying a
    `chain` but no `kind` is checked as a single exchange and fails
    `inclusion` (receipt absent). An implementer keying on the presence of
    `chain` would route those two cases the other way round.
    """
    return pkg.get("kind") == "job"


def decode_hex_field(entry, name, step_name):
    """Decode a needed `request_hex`/`response_hex` member. Fails `evidence`."""
    v = entry.get(name)
    if not is_str(v):
        raise Fail("evidence", "%s: %s is missing or not a string" % (step_name, name))
    if len(v) % 2 != 0 or HEX_RE.fullmatch(v) is None:
        raise Fail("evidence", "%s: %s is not valid hex" % (step_name, name))
    return bytes.fromhex(v)


def step_name(idx, count):
    if idx == 0:
        return "step 1 (submit)"
    if idx == count - 1:
        return "step %d (fetch)" % (idx + 1)
    return "step %d (poll %d)" % (idx + 1, idx)


def job_link(step, reason):
    return Fail("job_link", "%s: %s" % (step, reason))


def decode_body_json(body, step, what):
    """Decode an authenticated response body "as integer JSON" (job_link)."""
    try:
        value = strict_json_loads(body)
    except JsonError as e:
        raise job_link(step, "%s body is not valid integer JSON: %s" % (what, e))
    # FORMAT-GAP: "Decode its **authenticated response body** as integer
    # JSON. Take `job_id` from that body" / "A poll's authenticated body is
    # integer JSON: every poll ... must have `state:"pending"`". The text
    # does not say what a body that is valid JSON but not an object does.
    # Choice: a non-object body has no `job_id`/`state` member and fails
    # `job_link`, the same link as a wrong member.
    if not isinstance(value, dict):
        raise job_link(step, "%s body is not a JSON object" % what)
    return value


def run_job_chain(pkg, request_path, response_path, trust_path, ctx):
    """Chain checks for a verified `kind:"job"` package. Returns the PASS dict."""
    # Chain step 1 (evidence) ------------------------------------------------
    chain = pkg.get("chain")
    if not isinstance(chain, list):
        raise Fail("evidence", "job package has no chain array")
    count = len(chain)
    if not (CHAIN_MIN <= count <= CHAIN_MAX):
        raise Fail("evidence", "chain must have %d through %d entries, got %d" % (CHAIN_MIN, CHAIN_MAX, count))
    outer_id = pkg.get("receipt_id")
    # FORMAT-GAP: for a verified job package the text's chain step 1 names
    # only `evidence` checks (v1, chain array of 3-10 entries) and the
    # virtual package of each entry gets `receipt_id = entry.receipt.record.
    # job_id`, not the outer id; the outer id is bound at `job_link` ("require
    # its record.job_id to equal the outer receipt_id"). Only "Unverified/
    # pending input uses the existing single-exchange outer checks before
    # attempting any chain checks." Choice: the outer step-2 receipt_match
    # (outer receipt_id against the client response header) is NOT run first
    # for a verified job package. Consequently a fetch substituted from
    # another job passes its own exchange checks (its header equals its own
    # record.job_id) and then fails `job_link`, not `receipt_match`. An
    # implementer who keeps steps 1-3 in front of the branch reports
    # `receipt_match` for that case.

    seen_sessions = []
    job_id = None
    done_digest = None
    final_facts = None

    for idx, entry in enumerate(chain):
        step = step_name(idx, count)
        is_submit = idx == 0
        is_fetch = idx == count - 1
        is_last_poll = idx == count - 2

        # Chain step 2: decode needed public HTTP representations (evidence)
        if not isinstance(entry, dict):
            # FORMAT-GAP: the text does not say what a non-object chain entry
            # does. Choice: its needed hex fields are "missing", so `evidence`.
            raise Fail("evidence", "%s: chain entry is not an object" % step)
        if is_submit:
            # "The first `request_hex` is informational and ignored"
            request_loader = file_loader(request_path, "request_match", "request")
        else:
            request_loader = bytes_loader(decode_hex_field(entry, "request_hex", step))
        if is_fetch:
            # "The last `response_hex`, if present, is ignored"
            response_loader = file_loader(response_path, "evidence", "response")
        else:
            response_loader = bytes_loader(decode_hex_field(entry, "response_hex", step))

        # Construct the virtual single-exchange package.
        receipt = entry.get("receipt")
        record = receipt.get("record") if isinstance(receipt, dict) else None
        verdict = receipt.get("verdict") if isinstance(receipt, dict) else None
        rec_job_id = record.get("job_id") if isinstance(record, dict) else None
        verifier_pub = verdict.get("verifier_pub") if isinstance(verdict, dict) else None
        # FORMAT-GAP: "receipt_id = entry.receipt.record.job_id". When that
        # member cannot be read (receipt/record missing or not objects, job_id
        # not a string) the text gives no value. Choice: fall back to the outer
        # receipt_id so the entry fails at its ordinary decoding link
        # (`inclusion`) rather than at the virtual step-2 receipt_match.
        virtual = {
            "v": 1,
            "state": "verified",
            "receipt_id": rec_job_id if is_str(rec_job_id) else outer_id,
            "witness_key_id": verifier_pub,
        }
        if "receipt" in entry:
            virtual["receipt"] = receipt
        if "operator_statement" in entry:
            virtual["operator_statement"] = entry["operator_statement"]
        path_override = None
        if not is_submit:
            # "For later entries only, use the signed exchange's request.path
            # as the temporary destination path"
            req_obj = record.get("request") if isinstance(record, dict) else None
            p = req_obj.get("path") if isinstance(req_obj, dict) else None
            # An unreadable path leaves the trust path in place; such an
            # entry fails `inclusion` before the destination step anyway.
            path_override = p if is_str(p) else None

        try:
            facts = single_exchange_checks(virtual, request_loader, response_loader, trust_path, path_override, ctx)
        except Fail as e:
            # "A failure reason identifies the step when an individual
            # exchange fails." The link is retained.
            raise Fail(e.link, "%s: %s" % (step, e.reason))
        except Unverified:
            # Cannot happen: the virtual package is state verified.
            raise Fail("evidence", "%s: virtual package returned UNVERIFIED" % step)

        rec = facts["record"]
        ver = facts["verdict"]

        # Chain step 3 (job_link): outer id and distinct sessions ----------
        # FORMAT-GAP: the ordered list reads as per-entry ("After each
        # individual exchange passes, require ...", "For submit ...", "For each
        # later entry ..."). Choice: for each entry run its exchange checks,
        # then its job_link checks, then its protocol checks, before moving to
        # the next entry. A phased implementer (all exchanges first, then all
        # job_link checks) reports a later entry's exchange failure ahead of
        # an earlier entry's job_link failure.
        if rec["job_id"] != outer_id:
            raise job_link(step, "record.job_id does not equal the outer receipt_id")
        if ver["session_id"] in seen_sessions:
            raise job_link(step, "witness session_id repeats an earlier step's session")
        seen_sessions.append(ver["session_id"])

        req = rec["request"]
        resp = rec["response"]
        if is_submit:
            # Chain step 4 (job_link) ----------------------------------------
            if req["method"] != "POST":
                raise job_link(step, "submit method is not POST")
            if req["path"] != "/jobs":
                raise job_link(step, "submit target is not exactly /jobs")
            if resp["status"] != 201:
                raise job_link(step, "submit status is not 201")
            body = decode_body_json(facts["response_body"], step, "submit")
            jid = body.get("job_id")
            if not is_str(jid) or JOB_ID_RE.fullmatch(jid) is None:
                raise job_link(step, "submit body job_id is not a string of 1-128 ASCII letters, digits, '-' or '_'")
            job_id = jid
        else:
            # Chain step 5 (job_link) ----------------------------------------
            if req["method"] != "GET":
                raise job_link(step, "method is not GET")
            if req["body_bytes"] != 0 or facts["request_body"] != b"":
                raise job_link(step, "request body is not empty")
            if resp["status"] != 200:
                raise job_link(step, "status is not 200")
            expected_target = "/jobs/%s/%s" % (job_id, "result" if is_fetch else "poll")
            if req["path"] != expected_target or facts["request_target"] != expected_target.encode("utf-8"):
                raise job_link(step, "target is not exactly %s" % expected_target)
            if not is_fetch:
                body = decode_body_json(facts["response_body"], step, "poll")
                state = body.get("state")
                if is_last_poll:
                    # "the last must have state:"done" with a string digest";
                    # "exactly one final done poll and it immediately precedes
                    # fetch" follows from every earlier poll being pending.
                    if state != "done":
                        raise job_link(step, "final poll state is not 'done'")
                    digest = body.get("digest")
                    if not is_str(digest):
                        raise job_link(step, "final poll digest is not a string")
                    done_digest = digest
                else:
                    if state != "pending":
                        raise job_link(step, "non-final poll state is not 'pending'")
            else:
                # Chain step 6 (result_digest) ------------------------------
                # "H(the client's de-chunked fetched response body) must equal
                # the string digest from the authenticated done poll,
                # byte-for-byte": lowercase hex compared as an exact string.
                if sha256_hex(facts["response_body"]) != done_digest:
                    raise Fail("result_digest", "%s: fetched body hash does not equal the done poll digest" % step)
                final_facts = facts

    # "`witness_time` is the final fetch verdict's exact verified_at;
    # `witness_label` is the final selected witness's trust-list label."
    return {
        "result": "PASS",
        "witness_label": ctx["label"],
        "witness_time": final_facts["verdict"]["verified_at"],
        "profile": ctx["profile"],
    }


def run_check(evidence_path, request_path, response_path, trust_path):
    """Returns the result dict."""
    ctx = {"label": None, "profile": None}
    try:
        pkg = load_package(evidence_path)
        if is_job_package(pkg) and pkg.get("state") == "verified":
            # "Unverified/pending input uses the existing single-exchange
            # outer checks before attempting any chain checks." Only a
            # verified job package takes the chain path.
            return run_job_chain(pkg, request_path, response_path, trust_path, ctx)
        single_exchange_facts = single_exchange_checks(
            pkg,
            file_loader(request_path, "request_match", "request"),
            file_loader(response_path, "evidence", "response"),
            trust_path,
            None,
            ctx,
        )
        return {
            "result": "PASS",
            "witness_label": ctx["label"],
            "witness_time": single_exchange_facts["verdict"]["verified_at"],
            "profile": ctx["profile"],
        }
    except Unverified:
        return {"result": "UNVERIFIED", "witness_label": None, "profile": None}
    except Fail as e:
        return {"result": "FAIL", "link": e.link, "reason": e.reason, "witness_label": ctx["label"], "profile": ctx["profile"]}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

REJECTED_FLAGS = (
    "--expect-host", "--accept-revealed", "--ledger", "--epoch", "--epoch-paths",
    "--delivered", "--verifier-pub", "--receipt", "--seal",
)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    for a in argv:
        if a.split("=", 1)[0] in REJECTED_FLAGS:
            sys.stderr.write("error: %s is not accepted by the evidence interface\n" % a)
            return 2
    parser = argparse.ArgumentParser(prog="witness")
    sub = parser.add_subparsers(dest="command", required=True)
    chk = sub.add_parser("check")
    chk.add_argument("--evidence", required=True)
    chk.add_argument("--client-request", required=True)
    chk.add_argument("--client-response", required=True)
    chk.add_argument("--trust-list", required=True)
    args = parser.parse_args(argv)
    result = run_check(args.evidence, args.client_request, args.client_response, args.trust_list)
    sys.stdout.write(json.dumps(result, ensure_ascii=False) + "\n")
    return 0 if result["result"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
