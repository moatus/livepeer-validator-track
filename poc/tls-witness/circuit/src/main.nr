// The withheld Authorization header value holds no CR or LF, and it is the
// value tlsn committed to: SHA-256(value || blinder) == committed_hash, with a
// 16-byte blinder.
//
// `input` is value || blinder followed by zero padding. Only the first `len`
// bytes are checked; the blinder may hold any byte. `len` is public, and the
// verifier already knows it as the size of the withheld span. The proof is
// built with zero knowledge, so it reveals nothing else about the value.

// Longest value the circuit takes.
global MAX: u32 = 240;
global SIZE: u32 = MAX + 16;

mod tests;

fn main(committed_hash: pub [u8; 32], len: pub u32, input: [u8; SIZE]) {
    assert(len <= MAX, "value longer than the circuit takes");
    for i in 0..MAX {
        if i < len {
            assert(input[i] != 13, "CR in the withheld value");
            assert(input[i] != 10, "LF in the withheld value");
        }
    }
    let computed = sha256::sha256_var(input, len + 16);
    assert(computed == committed_hash, "value does not match the commitment");
}
