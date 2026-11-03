//! Stops the build, naming the step, when patch/apply.sh has not been run.
//! The workspace's build.rs pins the applied lib.rs itself.

const SRC: &str = "../apply.sh.out/tlsn-mux/src/lib.rs";

fn main() {
    println!("cargo:rerun-if-changed={SRC}");
    if !std::path::Path::new(SRC).exists() {
        panic!("the patched tlsn-mux source is missing. From the repository root, run:\n  sh patch/apply.sh");
    }
}
