# Router evidence interchange

This document is sufficient to implement the offline router checker. It does
not describe the older customer-seal interface. No operator filesystem,
transcript, certificate download, ledger, network service or private key is
an input. The checker trusts a witness's signed statement of its TLSNotary
verification; this package is not a portable TLSNotary proof.

## Inputs and outputs

Four files suffice:

```
witness check --evidence package.json --client-request request.http \
  --client-response response.http --trust-list trust.json
```

`request.http` and `response.http` are the client's retained raw HTTP/1.x
messages, including headers, framing and bodies. They are binary files, not
JSON strings. The response includes exactly one `X-Witness-Receipt` header.
The request is the router ingress request, so its Host can name the router;
the upstream destination is pinned by the client's trust policy below.

The result is JSON: `{"result":"PASS","witness_label":"...","witness_time":"2026-11-02T10:17:06Z","profile":"full-disclosure-fixture"}`, or
`{"result":"FAIL","link":"...","reason":"...","witness_label":null,"profile":null}`,
or `{"result":"UNVERIFIED","witness_label":null,"profile":null}`. After a trusted witness
has been selected, FAIL includes its label and the signature-authenticated
`profile`, even if trust policy subsequently rejects that profile. Before that
point `profile` is null; UNVERIFIED also returns null. For a job chain, report
the profile of the final checked entry (the fetch on PASS).
For chain FAIL, an invoked exchange check supplies its own label/profile (both null before its witness selection); a hex-decoding failure before that invocation retains the preceding entry's label/profile. A non-object chain entry also fails `evidence` without resetting the preceding label/profile, while a chain-length failure occurs before any entry and reports both null. Reasons are explanatory, not
stable comparison strings. A checker reports the first failing link below.
Exit status is 0 only for PASS, 1 for FAIL and UNVERIFIED. `expected.json`
in each sample gives `result`, `link` and `profile`; `link:null` means no failure link.
PASS output omits `link` and returns `witness_time` exactly as the signed
`verdict.verified_at` string, without normalization. UNVERIFIED/FAIL omit
`witness_time`. Compare result/link/profile rather than whole JSON objects.

PASS means the retained bytes match the exchange authenticated by the trusted
witness, including the operator's signed binding to this receipt. It does not
mean client authorization, fresh inference, or witness independence. Labels
are local trust-list descriptions, not evidence of independence.

## JSON, hashes and signatures

JSON is UTF-8. Reject invalid JSON, NaN/Infinity, unpaired Unicode surrogates,
and any number containing `.`, `e` or `E`, at the active read/parse link.
Negative zero (`-0`) is also rejected. Numbers must fit an integer in [-2^63, 2^64-1]; typed unsigned fields reject
negative values at their decoding link. This rule also covers unknown members.
Duplicate member names resolve to the last value, before hashing or checking.
Producers must emit unique names and nonnegative integers in known fields.

Define `C(x)` recursively:

- Object: sort names lexicographically by Unicode scalar value (equivalently
  UTF-8 byte ordering for valid Unicode), emit `{`, quoted name, `:`, value,
  comma between entries, then `}`. No whitespace.
- Array: keep order, recursively encode values with commas inside `[]`.
- String: JSON quotes, escape quote as `\"`, backslash as `\\`, backspace,
  tab, LF, form feed and CR as `\b`, `\t`, `\n`, `\f`, `\r`. Other U+0000
  through U+001F use lowercase `\u00xx`. All other characters are literal
  UTF-8, including `/`, U+2028 and non-ASCII letters. No normalization.
- Integer: decimal digits without leading zeros, except zero itself;
  negatives use a leading `-` followed by the magnitude (no negative zero).
  Booleans and null: `true`, `false`, `null`.

Thus Python's `json.dumps(x, sort_keys=True, separators=(',', ':'),
ensure_ascii=False).encode('utf-8')` gives C for this supported subset.
Transport indentation and JSON member order do not affect C.

`H(bytes)` is SHA-256, represented as 64 lowercase hexadecimal characters.
All body lengths count bytes, not characters. All digests are of the exact
bytes described here; there is no extra newline or domain prefix unless
explicitly given. A public key is the raw 32-byte Ed25519 verifying key,
encoded as 64 hex characters (producers use lowercase). A signature is the
raw 64-byte Ed25519 signature, encoded as 128 hex characters. No PEM, DER,
base64 or Ed25519ph. Keys, signatures and Merkle siblings decode hex in any
case. Other hashes in records are decoded as strings, without a hex-shape
check at inclusion; recomputed lowercase digests are compared as exact strings
at the comparing link (`operator_identity`, `request_match`,
`forwarded_headers`, or `response_delivery`). An uppercase digest with letters
therefore fails that comparison. `root` must equal the computed lowercase hex
exactly at `inclusion`. Trust-list matching is exact even for key strings.

Use strict Ed25519 as in Rust's `ed25519_dalek::verify_strict`: verify the
cofactorless equation `[S]B = R + [k]A`, with k the standard Ed25519 challenge.
Reject S >= L. Decode A and R as Edwards25519 points; reject failed decoding
or if `[8]A` or `[8]R` is the identity. Compare the canonical encoding of the
computed R with the signature's R encoding (thus rejecting a noncanonical R).
A is decoded with the Edwards25519 field decoder; no additional re-encoding
check of A is required. Common libraries, including OpenSSL through Python
`cryptography`, accept the identity-key universal forgery (A = identity,
R = identity, S = 0) and need an explicit small-order check. A library verify
call alone does not establish this rule. The `identity-key-forgery` sample
is deliberately labelled TEST ONLY and must fail `witness_signature`.

For **each signed object**, remove only its top-level `sig` member and verify
`sig` over `C(the remaining object)`. This includes its public-key member,
version, timestamp if present, and every unknown extension member. Never
remove `sig` recursively. Conversely, a hash of a signed statement includes
its `sig`. Never reconstruct a signed object from selected fields.

## Package layout

GET `/evidence/RECEIPT_ID` returns this JSON object directly, without an archive
or external references. A verified package contains:

| Member | Type / meaning |
| --- | --- |
| `v` | integer, 1 |
| `receipt_id` | string, router-generated 16 random bytes as 32 lowercase hex; also delivered in the response header |
| `state` | `pending`, `verified`, or `unverified` |
| `created_at` | string, operator UTC RFC3339 time with milliseconds |
| `deadline_seconds` | integer, currently 240; operator evidence deadline |
| `terminal_at` | string, operator UTC RFC3339 time with milliseconds, emitted for terminal outcomes |
| `reason` | optional string, operator explanation for pending/unverified; removed on verified completion |
| `witness_key_id` | for verified packages, string equal byte-for-byte to `receipt.verdict.verifier_pub`; the full public-key hex is the identifier |
| `operator_statement` | signed object described below; may also appear in pending/unverified packages |
| `receipt` | object described below, required for verified, absent for honest unverified outcomes |

The outer object is **unsigned**. Times, deadline, reason and state are the
operator's account. Only `v`, state, receipt id, and witness identifier enter
the checks below; metadata is not validated as a signed fact. An operator
can suppress evidence or replace a package with an unverified outcome; that
cannot establish misrouting or a verified exchange. Pending is always FAIL,
never UNVERIFIED. Unknown outer members are ignored.

`receipt` fields:

| Member | Type / meaning |
| --- | --- |
| `v` | integer, 1 |
| `record` | one complete exchange record below |
| `path` | array of sibling hashes (hex, 32 bytes each), bottom-up |
| `verdict` | witness-signed session verdict below |

`record` fields (required except as listed explicitly below):

| Member | Type / meaning |
| --- | --- |
| `session_id` | opaque string, witness-issued session identifier |
| `operator_pub` | string, signing public key of operator statement |
| `operator_statement_sha256` | H(C(operator_statement)), **including its signature** |
| `n` | positive integer, 1-based exchange index; router currently emits 1 |
| `job_id` | string equal to receipt_id; witnessed X-Job-Id value |
| `outcome` | string, must be `verified` |
| `request` | object: `method`, `host`, `path` (strings), `body_sha256` (hex hash), `body_bytes` (nonnegative integer), `forwarded_headers_sha256` (hex hash) |
| `response` | object: `status` (integer 0–65535), `content_type` (string or null), `body_sha256` (hex hash), `body_bytes` (nonnegative integer), `transfer` (string, emitted `identity` or `chunked`), optional `images` (array below) |
| `salt` | string, 32 random bytes encoded hex, included in the leaf hash |

`request.withheld` is required as a non-null object for `credential-hidden`:
`{header:string,start:integer,end:integer,no_cr_lf:string}`. `header` must be
exactly `authorization` or `x-api-key`; this is a byte-for-byte comparison without case folding or trimming, and witnesses sign the lowercased wire name.
A missing/non-string header fails
`inclusion`, an unsupported string fails `session`. Both offsets are unsigned 64-bit
integers; start must be less than end.
An array of header names or any other non-string `header` is ill-typed and fails `inclusion` before witness selection.
The complete offset policy is `start < end`; offsets are not compared with the retained ingress request, and no additional upper bound on end is enforced. `no_cr_lf` must equal one of these
SHA-256 hashes of the unchanged compiled credential-value no-CR/LF circuits:

- `431064964f5d2f0f987d2f1a4d38e1c946065a0de9f9e2fbff2a09082a1edd1c`
- `504c3254ea2da2cbbce48ca37953cb591710ad1b4a494ac5cb5858050d77ad3d`
- `a59c1d2d199d0ff0a660314fd08df73b417e9b1ebee23be7d30675474ff79c57`
- `f475261ee6fba85d17dddbd4d183fcc925ff791ceb3c6d969c078214af7dd342`

The `no_cr_lf` value is compared as an exact string against the listed lowercase hashes; uppercase variants fail `session`.
Within `session`, time is checked before session identity and profile acceptance, followed by the withheld presence/header/range/circuit predicate; all its failures share `session` and explanatory reasons do not establish a separate priority between the predicate's terms.
Extra members of a well-typed withheld object are ignored by policy but remain part of the complete record hash.
For the other profiles, withheld must be absent or null.
The decoding rules apply before profile policy, so a header-only withheld object fails `inclusion` even under full disclosure. A malformed object
fails `inclusion`; a well-typed object with the wrong profile, offsets or
circuit or header fails `session`. The offsets disclose the selected credential
value's byte position and length (`end - start`) to the witness and every
evidence recipient; only its content is hidden.

The operator selects `--credential-header authorization` (default) or
`--credential-header x-api-key` on router/prover. `x-api-key` is accepted only
with credential-hidden. Authorization injects `Bearer ` plus the environment
credential; x-api-key injects exactly that credential, without a prefix. The
witness derives the placement from the authenticated public header name and
signs `request.withheld.header` in the exchange's Merkle leaf. The witness, rather than the offline checker, requires
exactly one supported credential header, with case-insensitive duplicate
rejection and rejection when both names occur. The name, colon and CRLF stay
public; exactly the value is authenticated, committed and proven free of CR/LF.
Host and Content-Length stay public; Transfer-Encoding remains public and is
rejected on requests. Every other request byte and the entire response are
revealed. Neither offline checker reads an upstream credential from the
retained ingress request: it checks the signed placement and proof metadata.
Trust policy has no client placement preference: the checker tests the signed header only against the two allowed names and does not compare it with the retained request.
For producers, `start` is the first credential value byte after colon whitespace and `end - start` is its complete wire value length, including `Bearer ` for authorization; offline checkers cannot verify this relationship.

Query-parameter placement is **unsupported**: the request target must stay
public to bind the sealed path, and the existing no-CR/LF predicate does not
constrain query delimiters or percent-encoding. Cookie placement is
**unsupported**: the predicate does not constrain cookie separators, duplicate
cookie names or interpretation. Secrets placed there, in other headers or in
the body are public. A response echoing the credential also reveals it; no
response secrecy or generic credential confidentiality is claimed.

Full disclosure sends the entire request
to witness software. A full-disclosure-fixture witness refuses to sign unless
every revealed Authorization value starts with `Bearer tlsw-fixture-`. This
is a fixture namespace check, not evidence that a value is safe for disclosure.
The offline checker never inspects Authorization in either retained HTTP file; the `Bearer tlsw-fixture-` prefix is enforced by the witness before signing.
`credential-sequence` identifies the gateway-specific obtain/use/disable/two-refusal/reveal producer path; the checker treats its transcript as fully disclosed and the signature does not certify global credential revocation.
No profile claims enclave isolation or attestation.
Actual credentials never appear in an honest package.

Each optional `response.images` element is an object with `media_type`
(string), `sha256` (hex hash of decoded image bytes), `bytes` (nonnegative
integer). Empty arrays are normally omitted. These are signed metadata;
the router checker checks the **entire delivered body**, not an extracted
image, and does not independently recompute image descriptors. `transfer`,
`salt` and limits likewise remain authenticated metadata, not extra policy
comparisons. Salt is required but is validated only as a string, not as hex.
`transfer` is required as a string but is not enum-checked; image hashes
are strings and not independently checked against extracted images. Counts and indexes use unsigned 64-bit integers on this build.

The exchange leaf is H(C(the **complete raw record object**)), including
salt, optional fields if present, and any extension fields. Do not remove
nulls, add defaults, omit empty arrays, or deserialize and reserialize a
selected schema before hashing. Known fields must have the types above;
unknown record members are included in the hash, but not interpreted.

`verdict` fields:

| Member | Type / meaning |
| --- | --- |
| `v` | unsigned 32-bit integer, 5 |
| `session_id` | string, same session as the record |
| `mode` | string, emitted `proxy` or `mpc`; authenticated metadata |
| `server_name` | string, DNS identity validated by the witness against its TLS root store |
| `exchanges` | nonnegative integer, total leaf count; at least 1 to include this record |
| `root` | lowercase hex hash, session Merkle root |
| `limits` | object with `max_sent`, `max_recv` nonnegative byte-count integers |
| `profile` | required string: `full-disclosure-fixture`, `credential-hidden`, or `credential-sequence`; accepted per witness in the trust list |
| `verified_at` | string, witness's **own** UTC RFC3339 time at signing, emitted to whole seconds |
| `verifier_pub` | witness public key, hex |
| `sig` | witness Ed25519 signature |

`verified_at` is inside the signature. The checker requires a calendar-valid RFC3339 date-time with four-digit year
and a literal uppercase `T` separator (space and lowercase `t` are rejected).
The entire string must be ASCII, including the numeric offset sign.
Seconds may be 00–60; optional fractions have one or more decimal digits.
Offsets may be `Z`, `z`, or numeric +/-HH:MM (HH <= 23, MM <= 59). There is
no leading/trailing whitespace. UTC whole seconds is a producer convention;
fractional seconds and non-UTC offsets are accepted. The checker sets no maximum age and compares neither it nor the operator's unsigned
times against a clock. The mode string is not a policy restriction here.

`operator_statement` fields:

| Member | Type / meaning |
| --- | --- |
| `v` | integer, emitted 1; included in the signature and hash |
| `session_id` | string, witness session for this attempt |
| `receipt_id` | string, router receipt id |
| `method`, `host`, `path` | strings describing the upstream request |
| `body_sha256`, `body_bytes` | hash and length of upstream request body |
| `forwarded_headers_sha256` | ordered forwarded header digest below |
| `operator_pub` | operator public key, hex |
| `sig` | operator Ed25519 signature |

The witness checks this statement against the actual witnessed request before
issuing the record. The checker independently compares all its binding fields.
The statement version is signed but is not separately version-gated by the
current checker. Unknown statement/verdict fields are signed and unknown
receipt fields are ignored.

At `inclusion`, every record/request/response/verdict field in the tables must
be present and have its listed type, with these exact exceptions:

| Member | Absent/null behaviour | Ill-typed present value |
| --- | --- | --- |
| record.operator_pub | decodes absent/null; fails `operator_identity` if earlier checks pass | `inclusion` |
| record.operator_statement_sha256 | decodes absent/null; fails `operator_identity` if earlier checks pass | `inclusion` |
| record.response.content_type | **absence fails inclusion**; null allowed only for an absent client Content-Type, otherwise `response_delivery` | `inclusion` |
| verdict.profile | absence/null fails `inclusion` | `inclusion` |
| record.request.withheld | absent/null valid only for full-disclosure-fixture or credential-sequence; otherwise `session` | `inclusion` |
| record.response.images | absent decodes as empty; null fails `inclusion` | `inclusion` |
| verdict.sig | absence decodes, then fails `witness_signature` | non-string, including null: `inclusion`; string with invalid hex/length/signature: `witness_signature` |

Unknown profile strings fail `inclusion`. Missing salt,
verified_at or limits fails `inclusion`. Limits must contain both byte counts.
All counts/indexes are unsigned 64-bit, verdict.v is unsigned 32-bit and
response.status unsigned 16-bit. At inclusion, hashes and key fields are
strings; decoded byte lengths are enforced only where used. Removing a field
from an already signed sample may fail its earlier hash/signature check;
these are decoding rules, not permission to skip ordered checks.
An absent/non-object outer operator_statement fails `operator_identity`.

## Merkle inclusion

Decode a sibling to 32 binary bytes. Set `h = H(C(record))`, `i = n-1`,
`count = verdict.exchanges`. Require `0 <= i < count`. While count > 1:

1. If `(i XOR 1) < count`, consume the next sibling s. If i is even,
   h = SHA256(`0x01 || h || s`); otherwise h = SHA256(`0x01 || s || h`).
2. Without a sibling at that level, carry h up unchanged.
3. Set i = floor(i/2), count = ceil(count/2).

Require exactly all siblings consumed and lowercase hex(h) equal to root.
An empty path for one leaf makes root equal to the leaf. No leaf prefix is
used. This description supports other counts even though router sessions
currently carry one exchange.

## Trust list

`trust.json` is the client's policy, supplied independently of the package:

```json
{
  "v": 1,
  "witnesses": [{"label": "chosen witness", "public_key": "64 hex characters", "profiles": ["full-disclosure-fixture"]}],
  "operators": ["64 hex characters"],
  "server_name": "test-server.io",
  "path": "/api/v1/chat/completions"
}
```

All five members are required; no other members are allowed. Each witness
entry has exactly `label` and `public_key` strings and a required `profiles`
array containing any subset of the three supported profile strings (duplicates allowed).
Unknown or non-string entries are a trust-list shape error at `witness_signature`; listing all three profiles is not required. An empty array accepts no profile. Operators is an array of
public-key strings. Multiple keys allow rotation; the selected witness label
and accepted profile list come from the last matching entry if duplicated. Empty witness/operator lists trust
no such identity. Matching key strings, server_name and path is exact and
case-sensitive; no DNS suffix, URL, case, port or path normalization. The
checker reads no files referenced by this JSON (there are no path fields).
The strings shown above as descriptions must be replaced with actual public
keys; the committed samples contain usable lists. There is no expiry or
revocation lookup. Trust-list key entries are strings without a separate hex
shape check; a malformed string cannot match a valid signed key. The evidence
interface rejects `--expect-host`, `--accept-revealed`, `--ledger`, `--epoch`,
`--epoch-paths`, `--delivered`, `--verifier-pub`, `--receipt` and `--seal`.
Policy comes from trust.json.

## HTTP interpretation

Parse a complete HTTP/1.0 or HTTP/1.1 message with at most 64 headers. Header
names are ASCII case-insensitive; **every header value must be UTF-8**, even
when not compared or forwarded. Request header errors fail `request_match`;
final response head errors fail `receipt_match` at step 2. Start lines and
header lines accept CRLF or bare LF, including mixed endings; bare CR is an
error. Header names are nonempty RFC 9110 tokens immediately followed by `:`.
Reject obsolete folding, whitespace before `:`, lines without `:`, embedded
CR, and control bytes other than HTAB in values. Leading empty lines before
the start line are accepted. Versions are exactly HTTP/1.0 or HTTP/1.1. Strip leading/trailing header-value SP and HTAB as ordinary HTTP
parsing does, retaining internal whitespace and order. Do not merge repeated
headers. Binary body bytes are never decoded or normalized.

For requests reject duplicate Content-Length or Transfer-Encoding and reject
having both. A single Content-Length of one or more ASCII digits (no sign or other
non-digit after SP/HTAB trimming) frames that many bytes; absent
both, the body is empty. A single Transfer-Encoding must be `chunked`
(case-insensitive). Reject unsupported Expect values (only case-insensitive 100-continue),
then parse body framing. Keep the method and request target literally from
the request line. Require the entire file consumed at request comparison.
The Host ingress header is not the upstream host comparison.

For responses first skip any leading informational messages whose bytes start
with `HTTP/1.1 100 `, each through its first CRLF CRLF. No other informational
status is supported. This prefix is literal: `HTTP/1.1 100\r\n` and
`HTTP/1.0 100 Continue` are intentionally not skipped. A missing terminator
leaves that head to fail later parsing. Status must be exactly three ASCII
digits, parsed numerically. The reason phrase is optional and not compared:
`HTTP/1.1 200`, `HTTP/1.1 200 ` and `HTTP/1.1 200 OK` are all valid status
lines. Reject duplicated
Transfer-Encoding, Content-Type or Content-Length when those fields are
consulted. A Transfer-Encoding value, trimmed and case-insensitive, must be
`chunked` and takes framing precedence over Content-Length. Otherwise 204
and 304 have empty bodies; otherwise Content-Length frames the body when
present; otherwise all bytes after the head form a close-delimited body.
Require no trailing bytes after this final message at response comparison.
Structural final-head errors (including missing terminator, malformed lines,
version, status width and more than 64 headers) fail `receipt_match` at step 2.
Framing errors and duplicate consulted framing/Content-Type headers fail
`response_delivery` at step 12. Content-Length uses the same digits-only rule
as requests. The Content-Type comparison is the parsed value exactly, or null
if absent; record.response.content_type must still be present.
No media-type normalization, decompression or JSON reserialization.

Bare LF is a line ending only in start lines and header lines. In chunked
bodies a line ends only at CRLF: the chunk-size line, the CRLF after chunk
data, each trailer line and the empty line that ends the trailers. A bare
LF there is not a line ending. It becomes part of the line's text: a size
line then fails as a framing error (`response_delivery` for a response,
`request_match` for a request), and inside a trailer line it is ignored
with the rest of that line. The 100 Continue skip is the literal CRLF CRLF
described above.

For chunked framing: parse a CRLF-terminated hex size (trim Unicode whitespace
from the UTF-8 size text; a leading `+` is accepted, a leading `-` is not),
ignore extensions after the first semicolon, take exactly that many data
bytes followed by CRLF. A zero chunk ends data; consume trailer lines through
the next empty line, ignoring their contents. Hash the concatenated data
bytes only. Chunk sizes, chunk extensions and trailers are not body bytes.

The forwarded digest is H(C(array of `[lowercase_name, value]` pairs)),
selecting only `content-type` and every name beginning `x-client-`, in wire
order, keeping duplicates. This includes `X-Client-Nonce` and
`X-Client-Require-Witness`. No sorting of this array. It excludes Host,
Authorization, framing headers and other non-forwarded client headers.
Example: `[["content-type","application/json"],["x-client-note","first"],
["x-client-note","second"]]` with no whitespace is the hash input.
Body hashes cover de-chunked request/response body bytes, not HTTP heads.

## Ordered checks and failure links

Each item stops immediately on error. There is no fallback from FAIL to
UNVERIFIED. A file read/parse error belongs to the link active at that point.
The failure links, the only stable values of `link`, are: `evidence`,
`evidence_pending`, `receipt_match`, `inclusion`, `witness_signature`,
`session`, `operator_identity`, `destination`, `request_match`,
`forwarded_headers` and `response_delivery`. `evidence_pending` is its own
link, not a reason under `evidence`.

1. **evidence**: Read package JSON and require `v == 1`. Read the response
   file and remove leading 100 Continue heads.
2. **receipt_match**: Parse the retained final response head. Require exactly
   one X-Witness-Receipt, a UTF-8 value. Require outer `receipt_id` equal to
   that value. This derives the client receipt id; do not trust only the
   package's id or take the id from an operator directory.
3. **evidence**: If state is `unverified` and the `receipt` member is
   **absent**, return UNVERIFIED now. Its reason is unproven; no trust-list,
   request, signatures or response body are checked on this early outcome.
   `receipt:null` is present and does not qualify. If state is `pending`,
   return FAIL with link `evidence_pending`. Only `verified` proceeds; every other
   state fails evidence. This step decides state only: a verified package
   whose receipt is absent, null or not an object fails `inclusion` at step 4.
4. **inclusion**: Decode receipt and known record/verdict field types; require
   receipt.v == 1, verdict.v == 5, record.outcome == `verified`, and the
   complete record's inclusion as described above. Bad hashes, index/count,
   path length, or root fail this link.
5. **witness_signature**: Verify verdict signature over the whole verdict
   minus sig. Read/parse the strict trust-list shape and require trust.v == 1.
   Require witness_key_id equal to verdict.verifier_pub and that exact key
   in trust.witnesses. Select its label.
6. **session**: Require valid RFC3339 verified_at, record.session_id equal
   to verdict.session_id, the signed verdict.profile accepted by the selected
   witness entry, and the profile-specific request.withheld rules above.
7. **receipt_match**: Require record.job_id equal to the client receipt id.
8. **operator_identity**: Verify operator_statement's signature. Require a
   trust.operators entry equal to BOTH record.operator_pub and
   statement.operator_pub. Require record.operator_statement_sha256 equal
   to H(C(the complete statement, including sig)). Compare statement fields
   with record fields: session_id, receipt_id (=job_id), method, host, path,
   body_sha256, body_bytes, forwarded_headers_sha256. Every mismatch fails
   this link, including substituting an older valid operator statement.
9. **destination**: Require verdict.server_name and record.request.host both
   equal trust.server_name, and record.request.path equal trust.path.
10. **request_match**: Read and parse the retained request, including all
    framing rules above. Require full file consumption, method and target
    equal to record.request.method/path, and body length and lowercase hash
    equal to record.request.body_bytes/body_sha256.
11. **forwarded_headers**: Hash the retained request's selected ordered
    headers and compare with record.request.forwarded_headers_sha256.
12. **response_delivery**: Read and parse the retained response (skipping
    100 Continue heads). Require full consumption and equality of final
    status, Content-Type (including null), body length and body hash with
    record.response.status/content_type/body_bytes/body_sha256.
13. **receipt_match**: Reconfirm the final response has exactly one receipt
    header equal to the client receipt id. Then report PASS with witness_label
    and witness_time (the signed verdict.verified_at).

No duplicate ledger is consulted or written. The same four inputs can be
checked repeatedly with the same result. The sample set includes all nine
ordinary substitutions, a swap with rewritten outer id, a nontrusted witness,
an older statement, nonce and no-nonce replay pairs, an unverified outcome, signature tampering, destination policy edits, pending
state, a present-null unverified receipt, the small-order forgery and HTTP
framing/encoding cases.
The normal samples are genuine current fixture captures: normal-a uses full-disclosure-fixture and normal-b uses credential-hidden; both share the operator host and establish no independent key custody.
The full-disclosure-* and credential-hidden-* families pin genuine receipts, altered request/response bytes, wrong trust destinations, receipt/session swaps, signed-profile edits and rejected profiles; all six withheld-* policy samples are re-signed verdicts labelled "TEST ONLY: local fixture test key", the nine x-api-key-* samples include x-api-key-placement-edit for header leaf binding, and job-later-entry-inclusion plus job-later-entry-hex and job-later-entry-nonobject pin reset versus retained chain label/profile (regenerate these policy/chain controls with `python3 -B tools/generate_policy_samples.py`, using only committed captures and a fresh in-memory test key).

## Replay limit

**Without a unique client-chosen nonce, an older matching request, response
and receipt PASS.** The witness's signed verified_at says when the witness
saw that exchange, but this checker imposes no freshness policy. The
`no-nonce-old-matching-receipt` sample intentionally reuses normal-a's old
matching files and passes. An older valid operator statement swapped into a
different receipt fails because the witness binds its complete hash and
session, not because of its age.

A fresh unpredictable `X-Client-Nonce` is forwarded and included in the
ordered header digest. Pairing a request bearing a new nonce with an older
receipt fails forwarded_headers, even with identical bodies. This binds the
exchange to that nonce-bearing request; it does not prove fresh inference,
client identity/authorization, or safety if the client reuses its nonce.

## Streaming and completion extension

A request asks for streaming when its retained JSON body has a top-level
`stream` member whose value is JSON boolean `true` (last duplicate wins).
The existing request-body hash authenticates that setting. The package and
receipt versions stay 1; the witness verdict stays 5.

**Delivery rule: body bytes.** The router removes upstream HTTP transfer
coding and emits new HTTP/1.1 chunked framing to the client. Every payload
byte is preserved, including SSE comments, whitespace, line endings, event
ordering and `[DONE]`. The router never parses and reserializes SSE events.
Upstream chunk boundaries, size extensions, trailers and HTTP heads are not
body bytes. The checker's existing response framing parser removes the
client-side chunk coding and compares the entire resulting body, its length,
status and Content-Type against the witness record. Chunk boundaries may
change without changing this claim. This rule reuses the existing signed
body digest and HTTP framing rules; it needs no second interpretation of a
signed raw stream. It does not authenticate arbitrary response headers.

The outer `delivery` object is **unsigned operator metadata** and is **not
consulted by `check`**. Its informational members are `rule` (body),
`complete`, `client_disconnected`, `cancelled`, `socket_accepted_body_bytes`,
`socket_accepted_body_sha256`, and the elapsed millisecond measurements
`first_chunk_ms` / `total_ms` (null if unobserved). The count/hash describe
body bytes accepted by socket writes, excluding framing. They cannot establish
what the client application consumed. The client's retained bytes, checked
against signed body length/hash and HTTP framing, decide delivery.

Consequently a verified streamed package with `delivery.complete:false` and
complete matching retained bytes **passes**. The committed
`samples/evidence/streamed-incomplete-metadata` pins this result in both
checkers. Metadata cannot veto or replace the signed-byte comparison.

An incomplete retained chunked response, a missing terminal zero chunk, a
short body or changed SSE byte fails **response_delivery** when checked
against a verified package. The ordinary early UNVERIFIED rule still applies
before inspecting the body when state is unverified and receipt is absent.
Socket acceptance is not an application acknowledgment: the router
cannot know which buffered bytes the client application consumed. The
prefix count/hash records bytes successfully accepted by socket writes,
excluding all framing. The client's own retained response is authoritative
for what it received; no stronger delivery acknowledgment is claimed.

**Failure outcomes and lifecycle.** No case below automatically repeats an
upstream inference call. Pending remains FAIL(evidence_pending).

- On a client write error or a two-second timeout on an individual socket write, set `client_disconnected:true`, stop writing, and
  continue reading upstream to its end unless the witness or deadline stops
  it. Disable, confirm two consecutive 401s and complete proof when possible.
  The terminal package is `state:unverified`, with no `receipt`; a completed
  witness record may be retained as `witnessed_receipt` for inspection only.
  The checker does not use that extension to establish completed delivery.
- A witness drop ends unverified, with no receipt. Disable and attempt the
  ordinary two-refusal gate outside routing cancellation. `credential_cleanup`
  states `dead_confirmed`, `death_unconfirmed`, or `cleanup_failed` as observed.
- `--evidence-deadline` (default 240 seconds, positive) cancels the actual
  routing future and its witness session transport, closes client delivery,
  and sets `cancelled:true`. No proof/reveal or upstream reading continues
  in that future. Bounded credential management cleanup and refusal probes
  run afterward; terminal publication waits for them. Thus terminal evidence
  can arrive after the routing deadline, by the bounded cleanup duration.
- On restart, every pending admitted receipt becomes unverified with a
  restart reason and terminal_at. A journaled provider hash is disabled and
  read back before serving evidence. `disabled_confirmed` means the management
  API read back `disabled:true`, **not** that two authentication refusals were
  reprobed. The credential value is never persisted, so such a post-crash
  probe is unavailable. Failure is `cleanup_failed`; absent durable identifiers
  are explicitly `unknown`. A crash during create before its response/hash
  can be journaled cannot guarantee cleanup; this is a stated limit, not
  dead confirmation. The bounded live runner separately discovers such keys
  from provider listings. Recovery scans both the current admission log and evidence directories, so
  pending evidence absent from the current log is also resolved. No pending
  receipt survives startup reconciliation.

Outer reasons, delivery facts and `credential_cleanup` are retrievable
operator claims, not witness-signed causes. Missing evidence remains
unverified, not misrouting. Existing terminal packages are preserved across
restart. A completed delivery followed by a crash before proof stays
unverified, even though the client got every response byte.

**Admission and reconciliation.** Before any upstream-capable task starts,
append one JSON line `{receipt_id,admitted_at}` and fsync the append-only
`--admission-log` path (default RECORD_DIR/admissions.jsonl). A log append
failure admits no upstream call. This log is local operator accounting; it
cannot expose a request omitted from both log and evidence. Run:

```
witness reconcile --admission-log admissions.jsonl --record-dir receipts
```

It reports each admitted id's `outcome` (`verified`, `unverified`, `pending`,
`missing`, or the stored invalid state), reason, delivery and cleanup claims,
plus `without_terminal_outcome`. Exit 0 requires every logged id to have a
matching terminal outcome; missing/malformed packages count as missing.
Recovery also creates an unverified outcome for an admission logged before
initial evidence creation. An unterminated final log line is reported on stderr as torn and is not
counted as an admission, even if its JSON is valid. Reconciliation continues
through all complete lines. Before accepting new requests, startup discards
that uncommitted torn suffix and fsyncs the log so later appends remain
separate complete lines. A malformed newline-terminated line anywhere
fails the command/startup loudly rather than silently dropping an id. Neither the log nor reconciliation is a signed
count of all customer requests.

`--max-dead-check-attempts` (default 20, positive) bounds the total number of
refusal probes per session, including interrupted and repeated gates. Budget
exhaustion ends unverified without reveal; disable still runs. A bounded paid
runner reserves this worst-case request count plus the single inference
before starting the session. This limit can end the gate before its 10-second
maximum; it cannot turn fewer than two consecutive 401s into a reveal.

## Multi-connection job extension

This section adds the fixture job protocol. All preceding single-exchange
rules remain unchanged. The same four client inputs and CLI flags suffice.
A verified job package has `v:1`, `kind:"job"`, `state:"verified"`, one
`receipt_id`, and a `chain` array instead of the outer `receipt`,
`operator_statement` and `witness_key_id`. Other outer metadata has the same
unsigned, informational meaning. Pending and unverified packages follow the
existing receipt-id/state checks; an honest unverified job has no outer
`receipt` or `chain`. Dropping a chain cannot produce PASS.

The client sends POST `/jobs` to the router and retains that original raw
request, the final fetch HTTP response (including X-Witness-Receipt), the
retrieved package, and its own trust list. It need not retain individual
submit/poll exchanges, manage credentials, interpret job ids or poll upstream.
The router runs the upstream job and returns its result as the original
request's response. HTTP libraries may reconstruct equivalent HTTP framing
under the preceding body/framing rules. There is no application acknowledgment,
freshness guarantee or new independence claim.

The trust list has exactly the existing schema; `path` is `/jobs` and
`server_name` pins the fixture TLS identity. Every witness in the chain must
be on `witnesses`, and every operator must be in `operators`. The one receipt
id is a router admission id, distinct from the upstream-generated job id.

### Chain representation

There are 3 through 10 ordered entries: submit, 1 through 8 polls, fetch.
Each entry contains:

- `receipt`: exactly the existing v1 inclusion receipt containing its signed
  v5 witness verdict and complete exchange record;
- `operator_statement`: exactly the existing signed request statement for
  that session, bound by that exchange's operator_statement_sha256;
- `request_hex`: hex-encoded public HTTP request bytes, without the injected credential header;
  `credential-sequence` fully discloses that header to the witness but omits it from this retained public request, and its signed `withheld` must still be absent or null;
- `response_hex`: hex-encoded HTTP response bytes for submit and each poll.
  The final fetch response comes from the client's response file instead.

Hex decoding accepts either letter case; invalid/missing needed hex fields
fail `evidence`. The first `request_hex` is informational and ignored:
submit is checked against the client's own request file. The last
`response_hex`, if present, is ignored: fetch is checked against the client's
own response file. No encoded private credential or management response is
included. Public representations use ordinary HTTP framing, the authenticated
Content-Type/status and full de-chunked bodies. Each embedded response has one
X-Witness-Receipt header carrying that step's exchange `job_id` (the router
admission id). Its value is checked under the existing rules. Request
forwarded-header hashing follows the existing filter, including the client's
nonce on submit. Later GETs have empty bodies and no forwarded headers in the
producer; the checker uses the actual signed header hash as usual.

### Ordered checks and additional links

The extension adds **`job_link`** and **`result_digest`** to the preceding
failure-link list. All existing links retain their existing meanings for each
individual exchange. A failure reason identifies the step when an individual
exchange fails. Check in this order:

1. Parse the whole package using the existing integer JSON rules (`evidence`).
   Require v1 and a chain array of 3–10 entries (`evidence`).
2. For each entry, in order, decode its needed public HTTP representations
   (`evidence`). Select the client's request for submit, and the client's
   response for fetch, as above. Construct a virtual single-exchange package:
   v1, state verified, receipt_id = entry.receipt.record.job_id,
   witness_key_id = entry.receipt.verdict.verifier_pub, and the entry's
   receipt/operator_statement. Run **all** existing ordered single-exchange
   checks against these bytes and the client's trust list. For submit use
   the original trust-list path. For later entries only, use the signed
   exchange's request.path as the temporary destination path; the protocol
   check in the next step then enforces its exact value. Host policy is
   never relaxed. An individual-exchange failure retains its original link.
3. After each individual exchange passes, require its record.job_id to equal
   the outer receipt_id and its witness verdict session_id to differ from
   every preceding session_id (`job_link`). This requires distinct witnessed
   TLS sessions; the operational fixture counters separately measure TCP
   connections. Each entry's record/verdict/statement session identities
   were already checked by the individual-exchange checks.
4. For submit, require method POST, target exactly `/jobs` and status 201
   (`job_link`). Decode its **authenticated response body** as integer JSON.
   Take `job_id` from that body, requiring a string of 1–128 ASCII letters,
   digits, `-` or `_` (`job_link`). Never take it from outer metadata, an
   operator statement or a client hint.
5. For each later entry require GET, an empty request body, status 200 and
   the exact target `/jobs/JOB_ID/poll`, or `/jobs/JOB_ID/result` for the last
   entry (`job_link`). Substrings, query parameters, omitted ids and another
   job's target do not suffice. A poll's authenticated body is integer JSON:
   every poll except the last must have `state:"pending"`; the last must
   have `state:"done"` with a string `digest` (`job_link`). There must be
   exactly one final done poll and it immediately precedes fetch.
6. For fetch, H(the client's de-chunked fetched response body) must equal
   the string digest from the authenticated done poll, byte-for-byte
   (`result_digest`). Independently, the existing response_delivery check
   already required those bytes to equal the witnessed fetch body.

Return PASS only after all entries pass. `witness_time` is the final fetch
verdict's exact verified_at; `witness_label` is the final selected witness's
trust-list label and `profile` is that entry's signature-authenticated profile. The present producer uses one local witness; labels confer
no independence. Existing FAIL/UNVERIFIED exits and JSON output rules apply.
Unverified/pending input uses the existing single-exchange outer checks before
attempting any chain checks.

For a verified job, the outer receipt-id comparison is replaced by `job_link`:
each entry's virtual `receipt_id` is its own `record.job_id`, and the outer id
binds only at `job_link` (the client's fetch header is first compared with the
fetch entry's virtual id). `kind:"job"` with state verified selects the chain
path, not the presence of `chain`: without `chain` it fails `evidence`;
`chain` without `kind:"job"` takes the single-exchange path and, absent an
outer receipt, fails `inclusion`. Checks are interleaved per entry: decode
that entry, run its exchange checks, then its `job_link` and protocol checks,
before decoding or checking the next entry. Rust already follows these rules.

### Credentials, retention and limits

The producer chooses **per-step credentials**. Each TLS connection obtains a
new credential after witness admission, completes one request, disables the
credential and obtains two consecutive 401 responses at least 500 ms apart
within ten seconds, before revealing that session. A pending poll is also a
step with its own lifecycle. The fixture accepts any enabled fixture
credential for a job; there is no credential-to-job ownership policy. Job-id
and body-digest links, rather than credential equality, connect the steps.
The witness signature does not certify management retirement; that is the
router's run-recorded retirement policy, as for single exchanges.

Only public completed receipts and submit/poll HTTP representations are held
between steps. There is at most one active TLS session/credential per chain;
completed TLS sessions are closed. The router journals the current provider
hash in the parent receipt directory for startup retirement; it never journals
the secret. A failure ends the chain UNVERIFIED without repeating submit or
any failed step. Startup uses the existing disabled-readback recovery rule.
The evidence deadline covers the chain; bounded cleanup can finish afterward.
Poll waits are 100 ms after the preceding step, at most eight polls.

`retention.json` measures canonical encoded bytes of the public chain array
held so far, actual retained byte-buffer capacity plus outer-vector storage,
its peak, and process peak RSS. Completed entries are retained as canonical
byte buffers between sessions. Buffer capacity is not an allocator/heap
census; RSS includes the original client request, active TLS/proof work,
transient clones, JSON allocations and runtime overhead.
Session records separately retain obtain/dead timestamps and process RSS;
fixture-side records count submit/poll/fetch calls and authentication results.

Samples `job-complete` and `job-pending-done` are genuine local witnessed
chains; `job-other-poll` and `job-other-fetch` substitute real exchanges from
a second job: they fail `job_link` on the differing receipt id, before the
upstream job-id target check. `job-result-digest` wraps a genuinely witnessed
corrupt fixture result in an explicitly synthetic unsigned verified envelope:
its exchanges authenticate, but it fails `result_digest` because the fetched
body's hash differs from the done poll's digest. The honest router's package
is `job-bad-digest-unverified`, which returns UNVERIFIED while delivering the
bytes and naming the digest mismatch. `job-cut` is an honest unverified
admission after a signed submit. `job-missing-id` is a
**synthetic test control**: a poll target and both fixture attestations were
re-signed to isolate job_link. It is explicitly labelled in the package and
is not described as a TLSNotary observation. Trusting an operator-controlled
witness allows fabricated attestations; this remains the stated trust model.

`job-other-id-poll` and `job-other-id-fetch` use the same receipt id throughout
but synthetically re-sign a later request target to carry the second job's
upstream id; each fails `job_link` at the exact job-id target comparison.
These are labelled synthetic fixture signatures, not TLSNotary observations.
`job-kind-without-chain` fails `evidence`; `job-chain-without-kind` fails
`inclusion`. `job-interleaved-order` fails the earlier poll's receipt-id
`job_link` before the later fetch's tampered-record `inclusion` can be checked.
`job-complete` and `job-pending-done` pass every link.

The package's informational `credential_cleanup` and the router's local
`credential-cleanup.json` retain a list of `{step, outcome}` entries, one per
attempted step, rather than overwriting earlier cleanup results. These are
router observations, not witness-certified retirement claims.
