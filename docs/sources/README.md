# Litepaper source versions

The current research source is Doug Petkanics, *Livepeer 2.0 Litepaper*, **October 2026**, preserved as [the supplied 14-page PDF](litepaper-2026-10.pdf). It replaces September as the starting point, without rewriting historical evidence. Receipt and extraction date: 2026-10-09; the PDF states only a month, not a publication day. No public source URL was supplied, so this archive does not claim an upstream release location.

| Source | SHA-256 | Role |
| --- | --- | --- |
| `litepaper-2026-10.pdf` | `b438da2b7d25d3043a3387b9db262293c2a0ec7801a765e5a3a249759b41569a` | Authoritative October PDF, including diagrams |
| `../litepaper-2.0.md` | `3e4a385ec19837f4b506b01989fac62cc33f99f28411bc1258f10c065e29240e` | Page-labelled October text extraction |
| `litepaper-2026-09.md` | `5fc153408fb636d9750788ae987ada6daaa9fc3df3e44f70cadde51a6158fb71` | Exact 247-line September baseline used by historical EX-01 and Slice 1 |

Run `python3 docs/sources/extract_october.py` from the repository root with Python 3 and **Poppler pdftotext 24.02.0**. The script checks the PDF hash and extraction version, runs `pdftotext -layout -enc UTF-8`, replaces form-feed separators with labelled Markdown pages and removes only trailing whitespace at page ends. The source text is not corrected or reconstructed. Editorial headings and fences distinguish extraction metadata from the source. The output hash above pins line citations. A different extractor version requires an explicit source/citation review.

The PDF remains authoritative for page 7's flow diagram and page 8's emissions chart. Their visual content cannot be faithfully recovered from text extraction. October contains its own diagram/chart; September's references to unreleased external assets remain historical. October also retains conflicting wording: the page 7 diagram repeats a fee-ratio mint rule and $50M ceiling despite the scheduled-emissions prose; the appendix describes node distribution by work and score, while the body and reward formula specify MFS; the schedule-governance paragraph leaves options open while the appendix says ratchet-only. These are source ambiguities, not analyst corrections.

Historical `SRC-LP20 L…` citations mean September. Current `SRC-LP20-OCT L…` citations mean October. Do not silently reinterpret earlier experiments, source notes or completed reviews as tests of October. See [the bounded October reconciliation](../../experiments/m2/october-reconciliation/README.md) for what was rerun and what remains open.
