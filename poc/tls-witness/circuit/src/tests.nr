// Run with `nargo test`. Hashes are SHA-256(value || blinder), computed
// outside the circuit.

use crate::{main, MAX, SIZE};

global BLINDER: [u8; 16] = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16];

// value || blinder, then zero padding up to SIZE.
fn input<let N: u32>(value: [u8; N], blinder: [u8; 16]) -> [u8; SIZE] {
    let mut out: [u8; SIZE] = [0; SIZE];
    for i in 0..N {
        out[i] = value[i];
    }
    for i in 0..16 {
        out[N + i] = blinder[i];
    }
    out
}

// "Bearer " and a 73-byte credential: the length of an OpenRouter key.
global V80: str<80> = "Bearer phase1-dummy-secret-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx";
global V80_HASH: [u8; 32] = [232, 112, 168, 117, 115, 251, 131, 178, 205, 224, 26, 242, 65, 86, 179, 160, 20, 24, 253, 252, 213, 164, 255, 222, 78, 18, 62, 249, 79, 95, 131, 151];

#[test]
fn value_of_80_bytes_passes() {
    main(V80_HASH, 80, input(V80.as_bytes(), BLINDER));
}

#[test]
fn short_value_passes() {
    let value = "Bearer phase1-dummy-secret".as_bytes();
    main([65, 117, 190, 81, 71, 248, 245, 247, 103, 224, 112, 219, 191, 21, 255, 238, 239, 42, 169, 104, 131, 91, 183, 186, 180, 155, 175, 108, 186, 69, 208, 234], 26, input(value, BLINDER));
}

#[test]
fn value_of_max_length_passes() {
    let mut value: [u8; MAX] = [120; MAX];
    let bearer = "Bearer ".as_bytes();
    for i in 0..7 {
        value[i] = bearer[i];
    }
    main([159, 84, 64, 142, 45, 81, 70, 179, 198, 19, 89, 40, 54, 66, 207, 198, 137, 216, 210, 30, 63, 116, 213, 36, 191, 182, 188, 218, 180, 248, 206, 238], MAX, input(value, BLINDER));
}

// tlsn's blinder is random and may hold any byte.
#[test]
fn blinder_may_hold_cr_and_lf() {
    let blinder: [u8; 16] = [13, 10, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16];
    main([49, 66, 253, 161, 42, 238, 246, 84, 22, 41, 173, 22, 238, 155, 26, 88, 38, 50, 164, 39, 100, 169, 123, 12, 153, 198, 0, 48, 191, 93, 116, 243], 80, input(V80.as_bytes(), blinder));
}

// Bytes past value || blinder are not hashed and not checked.
#[test]
fn padding_is_ignored() {
    let mut padded = input(V80.as_bytes(), BLINDER);
    padded[96] = 13;
    padded[97] = 10;
    main(V80_HASH, 80, padded);
}

#[test(should_fail_with = "CR in the withheld value")]
fn cr_in_value_fails() {
    let value = "Bearer phase1-dummy\r\nX-Injected: 1xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx".as_bytes();
    main([139, 196, 116, 249, 193, 133, 137, 224, 44, 169, 4, 254, 146, 218, 119, 53, 200, 125, 172, 92, 91, 72, 121, 152, 80, 180, 176, 7, 46, 4, 158, 55], 80, input(value, BLINDER));
}

#[test(should_fail_with = "LF in the withheld value")]
fn lf_in_value_fails() {
    let value = "Bearer phase1-dummy\nX-Injected: 1xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx".as_bytes();
    main([19, 160, 158, 130, 87, 197, 138, 71, 96, 38, 151, 6, 180, 7, 192, 212, 16, 91, 111, 252, 180, 168, 52, 254, 13, 180, 44, 83, 124, 3, 212, 58], 80, input(value, BLINDER));
}

#[test(should_fail_with = "value does not match the commitment")]
fn wrong_blinder_fails() {
    let mut blinder = BLINDER;
    blinder[0] = 0;
    main(V80_HASH, 80, input(V80.as_bytes(), blinder));
}

// The length is public: a proof for a shorter span does not match the
// commitment to the whole span.
#[test(should_fail_with = "value does not match the commitment")]
fn wrong_length_fails() {
    main(V80_HASH, 79, input(V80.as_bytes(), BLINDER));
}

#[test(should_fail_with = "value longer than the circuit takes")]
fn value_over_max_fails() {
    main(V80_HASH, MAX + 1, input(V80.as_bytes(), BLINDER));
}
