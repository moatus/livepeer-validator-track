#!/usr/bin/env python3
"""Reproduce the page-labelled October text with Poppler pdftotext 24.02.0."""
import hashlib
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
PDF = HERE / 'litepaper-2026-10.pdf'
PDF_SHA256 = 'b438da2b7d25d3043a3387b9db262293c2a0ec7801a765e5a3a249759b41569a'
OUTPUT = HERE.parent / 'litepaper-2.0.md'


def extract():
    if hashlib.sha256(PDF.read_bytes()).hexdigest() != PDF_SHA256:
        raise ValueError('October PDF differs from the pinned source')
    version = subprocess.run(['pdftotext', '-v'], capture_output=True, text=True, check=True).stderr
    if 'pdftotext version 24.02.0' not in version:
        raise RuntimeError('Use Poppler pdftotext 24.02.0 to preserve line citations')
    raw = subprocess.run(['pdftotext', '-layout', '-enc', 'UTF-8', str(PDF), '-'],
                         capture_output=True, text=True, check=True).stdout
    pages = raw.split('\f')
    if not pages[-1].strip():
        pages.pop()
    if len(pages) != 14:
        raise ValueError('Expected 14 PDF pages')
    header = ('# Livepeer 2.0 Litepaper — October 2026 source extraction\n\n'
              'Source: [original PDF](sources/litepaper-2026-10.pdf). SHA-256: `'+PDF_SHA256+'`.\n'
              'Extracted using Poppler pdftotext 24.02.0, `-layout -enc UTF-8`; page labels and code fences are editorial wrappers.\n'
              'Text within each page is the extracted source, including incomplete wording and PDF layout artifacts; diagrams remain authoritative in the PDF.\n'
              'See [provenance and reproduction](sources/README.md). September is preserved separately; old line citations do not refer to this version.\n\n')
    return header + '\n'.join(f'## PDF page {i}\n\n```text\n{page.rstrip()}\n```\n'
                               for i, page in enumerate(pages, 1))


if __name__ == '__main__':
    OUTPUT.write_text(extract(), encoding='utf-8')
    print(OUTPUT.name, hashlib.sha256(OUTPUT.read_bytes()).hexdigest())
