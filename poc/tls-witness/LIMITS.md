# TLS witness: behavior and limitations

The prototype verifies specific request/response claims. It is not a complete validator scoring mechanism. The [evidence format](EVIDENCE-FORMAT.md), [implementation](src/) and [sample packages](samples/evidence/) define the usable interface and its checks.

## What the evidence establishes

Under the configured trust policy, an accepted package binds a witnessed exchange to a certified upstream host, the operator's signed request association and the customer's retained request and delivered response. Streaming checks require completion evidence; fixture job-chain checks connect submit, poll and fetch exchanges and verify the result digest.

It does not establish which hidden model weights the upstream used, fresh computation, semantic output quality, economic purpose or customer independence. An authentic upstream can still misrepresent its internal execution. A signature authenticates the witness's statement; it does not establish independent control of that witness.

`FAIL` identifies an inconsistent or disallowed evidence link. `UNVERIFIED` indicates that the required evidence is unavailable or incomplete. Neither should automatically be interpreted as proven misrouting or dishonesty.

## Credentials and privacy

- **Credential-hidden:** reusable fixture credentials work without provider key-lifecycle calls. Authorization and x-api-key header values are supported; query and cookie credentials are not. Only Authorization has the reported workload sizing coverage. Portability to a real gateway using this reusable-credential path remains unestablished.
- **Response disclosure:** the witness sees customer content, the entire response, public framing, and the hidden credential's length and position. There is no response-side echo guard: an upstream that echoes the credential can expose it. This is not general prompt or credential privacy.
- **Credential-sequence:** provider-specific creation, retirement and refusal checks are required. Real-provider tests exercised temporary credentials, but a management success or refused probe does not establish universal revocation propagation. The witness does not certify credential retirement. Cleanup is bounded and can fail after process or host loss.
- **Full-disclosure fixture:** the software comparison exposes plaintext. It does not implement an enclave, hardware attestation or protection from the host administrator. Its cheaper path must not be presented as equivalent assurance to credential hiding.

## Compatibility and resource limits

The pinned TLSNotary integration uses TLS 1.2 and HTTP/1.1. It is not a drop-in path for arbitrary HTTP/2, HTTP/3 or upstream authentication schemes. The supported hidden header value is limited to 240 bytes. Check the command's configured send, receive, concurrency and deadline bounds against the intended workload.

Local experiments demonstrated text, streaming and substantial responses, but credential-hidden proof work remains expensive for the operator. The repeated hidden-input capacity result was 225 KiB on the tested Intel Core Ultra 7 155H setup; megabyte inputs were not established. This is a tested configuration boundary, not a universal service limit. Setup reuse improved small-request CPU cost without removing the cost of authenticating sent bytes.

Performance varied with host power state, concurrency, process reuse and memory limits. Full-disclosure and hidden-credential measurements are not interchangeable, and fixture throughput is not a real-provider service guarantee. Raw performance runs are not distributed with this package; measure the target environment before provisioning it.

## Routing, custody and deployment

Routing and offline checking have been implemented. Real-provider exchanges and local fixtures provide different evidence: fixture success cannot establish provider portability, and the multi-connection submit/poll/fetch workflow is a fixture protocol rather than general asynchronous API support.

Witness selection, operator admission, request association and customer-held delivery records are separate responsibilities. Several witnesses under common control do not demonstrate independence. A witness observing an upstream response alone does not prove customer delivery; the check requires the customer's retained bytes.

Before assigning economic consequences, a deployment still needs a credible witness-control arrangement, complete failure and missing-evidence reporting, retention and retrieval guarantees, and an operator response procedure. The [M3 evaluation](../../validator-track-workbench.html#M3.2) considers those responsibilities alongside the other verification approaches.

## Validation scope

The offline [sample suite](samples/evidence/) exercises accepted exchanges, tampering, trust/profile rejection, incomplete streaming and broken job links. Each fixture has its own expected outcome. Passing those checks establishes checker behavior on the supplied data; it does not rerun live provider experiments, demonstrate independent witness custody or establish production capacity.
