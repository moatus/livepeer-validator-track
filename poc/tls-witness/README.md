# TLS witness and verified request routing

This prototype forwards an HTTP request through a TLSNotary witness and produces evidence that binds the request, certified upstream host and returned response. A customer can check that evidence against the bytes it sent and received. It does not prove the upstream's hidden model weights, fresh inference, output quality or independent customer demand.

- [Evidence format and offline checking](EVIDENCE-FORMAT.md)
- [Supported behavior and limitations](LIMITS.md)
- [Validator mechanism evaluation](../../validator-track-workbench.html#M3.2)

## Build

The Rust workspace pins TLSNotary `v0.1.0-alpha.15`. The bundled patches and compiled credential-header circuit are required. From this directory:

```sh
mkdir -p target/barretenberg
curl -fL https://github.com/AztecProtocol/aztec-packages/releases/download/v4.2.0-aztecnr-rc.2/barretenberg-static-amd64-linux.tar.gz | tar -xz -C target/barretenberg
sh patch/apply.sh
cargo build --release
```

`build.rs` checks the static library and circuit hashes. The patched source is prepared from the Cargo cache; dependencies must be available before the offline patch step. Prover and verifier also need the pinned 32 MiB SRS, downloaded on first use if absent. The demonstrated build environment is x86-64 Linux with glibc.

## Commands and roles

Run `target/release/witness --help` and the relevant subcommand's `--help` for the complete flags.

| Command | Purpose |
| --- | --- |
| `verifier` | Admit TLS witnessing sessions and sign exchange evidence. Configure an explicit profile, trust roots, permitted upstream names and operator public keys. |
| `router` | Accept ordinary HTTP requests, select among configured witness endpoints and serve asynchronous evidence. Requires a profile, upstream host and operator key. |
| `reconcile` | Compare durable receipt admissions with their recorded outcomes. |
| `prover` | Make witnessed calls directly and write response and evidence records. |
| `seal` | Sign the customer's intended request for the sealed-request interface. |
| `check` | Check router evidence or sealed-request evidence against the customer's retained bytes and trust policy. |

The router returns an `X-Witness-Receipt` identifier. Customers retain their original HTTP request and response and retrieve the associated evidence. The [format specification](EVIDENCE-FORMAT.md) defines receipt lookup, terminal outcomes, streaming completion and the fixture submit/poll/fetch chain.

## Credential profiles

| Profile | Credential handling |
| --- | --- |
| `credential-hidden` | Reads `WITNESS_UPSTREAM_CREDENTIAL`; hides the configured Authorization or x-api-key header value from the witness transcript. The response and customer content remain visible to the witness. |
| `credential-sequence` | Obtains a temporary credential, makes the call and performs retirement checks before disclosure. Requires provider lifecycle request templates. |
| `full-disclosure-fixture` | Local-fixture comparison only. Requires a local PEM root and `WITNESS_FIXTURE_CREDENTIAL` starting with `tlsw-fixture-`; the witness sees plaintext. |

Configure credentials privately in the environment. The witness and router must use compatible profiles, and the customer trust list must explicitly allow the profile. Read [credential and trust limits](LIMITS.md#credentials-and-privacy) before choosing one.

## Check saved evidence offline

No provider call or private key is needed to check a retained evidence package:

```sh
python3 tools/cleanroom_check.py check \
  --evidence samples/evidence/body/package.json \
  --client-request samples/evidence/body/request.http \
  --client-response samples/evidence/body/response.http \
  --trust-list samples/evidence/body/trust.json
```

The Rust equivalent is `target/release/witness check` with the same four arguments. The checker emits `PASS`, `FAIL` or `UNVERIFIED`; only `PASS` exits successfully. Sample directories include an `expected.json` describing the expected result, failing link and profile. Some intentionally fail or remain unverified.

The evidence is a signed witness statement, not a portable TLSNotary proof. Trust-list keys and expected destinations must come from the customer's policy, not from an untrusted package. Generated run records can contain sensitive material; code, public sample evidence and format documentation are the distributed interface.
