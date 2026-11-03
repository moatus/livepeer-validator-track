#!/bin/bash
set -eu
# From this sensitivity directory. Offline numerical execution only.
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 ../2026-10-25-local-qwen/.venv/bin/python -B analyze.py
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 ../2026-10-25-local-qwen/.venv/bin/python -B verify.py
# No scoring/model/setup scripts are invoked.
