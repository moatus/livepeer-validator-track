//! Names the offline preparation step if patched source is missing.
fn main() {
    // Preserve the pinned crate's own build-script instruction.
    println!("cargo:rustc-check-cfg=cfg(tlsn_insecure)");
    let src = "../apply.sh.out/tlsn/src/session.rs";
    println!("cargo:rerun-if-changed={src}");
    assert!(std::path::Path::new(src).exists(), "patched tlsn source missing; run sh patch/apply.sh from the repository root");
}
