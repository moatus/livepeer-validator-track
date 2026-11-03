#!/bin/sh
# Builds the two patched crates that Cargo.toml's [patch] section points to,
# offline, from the local cargo cache: tlsn-mux at the revision Cargo.lock
# pins for tlsn v0.1.0-alpha.15, plus tlsn-mux-stream-cap.diff, which raises
# the per-connection stream cap from 512 to 4096; and tlsn at the pinned
# alpha.15 revision plus tlsn-session-frame-limit.diff (128 MiB frames).
# These are the two exceptions in SPEC section 3, rule 2.
# Output: patch/apply.sh.out/tlsn-mux (ignored), the source of the crate whose
# manifest is patch/tlsn-mux/Cargo.toml; and patch/apply.sh.out/tlsn, whose
# standalone manifest is patch/tlsn/Cargo.toml. Run from anywhere:
#   sh patch/apply.sh && cargo build --release
# The cargo cache needs tlsn-utils at REV, which any earlier build of this
# repository fetched. Without it, clone https://github.com/tlsnotary/tlsn-utils
# and set DB to its .git directory.
set -eu
cd "$(dirname "$0")/.."
REV=64722f7de999cbd41c0cab7312dade306d50ea5f
DB=${DB:-${CARGO_HOME:-$HOME/.cargo}/git/db/tlsn-utils-b5d34fca2ec7bc6b}
OUT=patch/apply.sh.out/tlsn-mux
UPSTREAM_SHA256=53cb363cae3ccbbf5d6a1c700a4a1331974f018eb4ac2f0a70974780671e46ce
PATCHED_SHA256=3cda73675714db13210b0b5e5248ac01cfd1cb291d8854e2723fc5d2e7bab69b

git --git-dir="$DB" cat-file -e "$REV^{commit}" 2>/dev/null || {
  echo "tlsn-utils $REV is not in $DB; see the header of $0" >&2
  exit 1
}
if [ ! -e "$OUT" ]; then
  mkdir -p "$OUT"
  git --git-dir="$DB" archive "$REV:mux/mux" | tar -x -C "$OUT"
  echo "$UPSTREAM_SHA256  $OUT/src/lib.rs" | sha256sum -c --quiet
  patch -s -p1 -d "$OUT" < patch/tlsn-mux-stream-cap.diff
fi
echo "$PATCHED_SHA256  $OUT/src/lib.rs" | sha256sum -c --quiet
echo "patched tlsn-mux in $OUT (max_num_streams 4096)"

# The second allowed diff: keep tlsn's session channel at 128 MiB. The
# committed standalone manifest only resolves inherited workspace fields.
REV=47aee45b53e06648c1b2ad3689b367b8c923fdec
DB=${TLSN_DB:-${CARGO_HOME:-$HOME/.cargo}/git/db/tlsn-b1de6072bd0608dd}
OUT=patch/apply.sh.out/tlsn
UPSTREAM_SHA256=31eb0694180427ea5226109f058411fdc4a39aa30ded9e90513721acbefea620
PATCHED_SHA256=d3fccd8aa668b9888ce5ba3c7fb045ea672b11f8711db0ea8c162b0aafb12d2a
git --git-dir="$DB" cat-file -e "$REV^{commit}" 2>/dev/null || {
  echo "pinned tlsn $REV is not in $DB" >&2
  exit 1
}
if [ ! -e "$OUT" ]; then
  mkdir -p "$OUT"
  git --git-dir="$DB" archive "$REV:crates/tlsn" | tar -x -C "$OUT"
  echo "$UPSTREAM_SHA256  $OUT/src/session.rs" | sha256sum -c --quiet
  patch -s -p1 -d "$OUT" < patch/tlsn-session-frame-limit.diff
fi
echo "$PATCHED_SHA256  $OUT/src/session.rs" | sha256sum -c --quiet
echo "patched tlsn in $OUT (session frame limit 128 MiB)"
