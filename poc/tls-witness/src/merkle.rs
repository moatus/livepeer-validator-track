//! Plain SHA-256 binary Merkle tree. A leaf is a 32-byte hash given by the
//! caller (the SHA-256 of a canonical exchange record, or a session's root);
//! a parent is SHA-256(0x01 || left || right). A node left without a sibling
//! at its level moves up unchanged. The root of no leaves is SHA-256 of
//! nothing. A leaf's place and the leaf count fix which side each sibling on
//! its path is on, so the path itself is just the sibling hashes, bottom up.

use anyhow::{Result, bail};
use sha2::{Digest, Sha256};

pub type Hash = [u8; 32];

fn parent(left: &Hash, right: &Hash) -> Hash {
    let mut h = Sha256::new();
    h.update([1u8]);
    h.update(left);
    h.update(right);
    h.finalize().into()
}

fn up(level: &[Hash]) -> Vec<Hash> {
    level
        .chunks(2)
        .map(|pair| match pair {
            [l, r] => parent(l, r),
            [only] => *only,
            _ => unreachable!("chunks of two"),
        })
        .collect()
}

pub fn root(leaves: &[Hash]) -> Hash {
    if leaves.is_empty() {
        return Sha256::digest([]).into();
    }
    let mut level = leaves.to_vec();
    while level.len() > 1 {
        level = up(&level);
    }
    level[0]
}

/// Every leaf's sibling hashes up to the root, from one pass over the tree.
pub fn paths(leaves: &[Hash]) -> Vec<Vec<Hash>> {
    let mut out = vec![Vec::new(); leaves.len()];
    let mut level = leaves.to_vec();
    let mut shift = 0;
    while level.len() > 1 {
        for (leaf, path) in out.iter_mut().enumerate() {
            let sibling = (leaf >> shift) ^ 1;
            if sibling < level.len() {
                path.push(level[sibling]);
            }
        }
        level = up(&level);
        shift += 1;
    }
    out
}

/// The root that `leaf`, at `index` of `count` leaves, and `path` give.
/// Fails if the path is not the length that place in that tree needs.
pub fn root_from_path(leaf: Hash, index: usize, count: usize, path: &[Hash]) -> Result<Hash> {
    if index >= count {
        bail!("leaf {} of a tree of {count}", index + 1);
    }
    let (mut hash, mut i, mut len, mut used) = (leaf, index, count, 0);
    while len > 1 {
        let sibling = i ^ 1;
        if sibling < len {
            let Some(s) = path.get(used) else {
                bail!("the path has {} hashes; leaf {} of {count} needs more", path.len(), index + 1);
            };
            hash = if i % 2 == 0 { parent(&hash, s) } else { parent(s, &hash) };
            used += 1;
        }
        i /= 2;
        len = len.div_ceil(2);
    }
    if used != path.len() {
        bail!("the path has {} hashes; leaf {} of {count} needs {used}", path.len(), index + 1);
    }
    Ok(hash)
}

pub fn from_hex(text: &str) -> Result<Hash> {
    hex::decode(text)
        .ok()
        .and_then(|b| b.try_into().ok())
        .ok_or_else(|| anyhow::anyhow!("{text:?} is not a 32-byte hex hash"))
}

#[cfg(test)]
mod tests {
    use super::*;

    // Every leaf of every tree up to 33 leaves proves against the root, and
    // a path for one place does not prove another. A wrong path here would
    // make every receipt fail or, worse, let one leaf pass for another.
    #[test]
    fn paths_prove_their_leaf_only() {
        for count in 1..=33usize {
            let leaves: Vec<Hash> = (0..count).map(|i| Sha256::digest(i.to_le_bytes()).into()).collect();
            let r = root(&leaves);
            let all = paths(&leaves);
            for i in 0..count {
                let p = &all[i];
                assert_eq!(root_from_path(leaves[i], i, count, p).unwrap(), r);
                let j = (i + 1) % count;
                if j != i {
                    assert!(root_from_path(leaves[j], i, count, p).map_or(true, |x| x != r));
                    assert!(root_from_path(leaves[i], j, count, p).map_or(true, |x| x != r));
                }
            }
        }
    }
}
