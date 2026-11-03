# Local Qwen extension

Read REPORT.md for results and limits. This directory is separate from the immutable original ../2026-10-25. No new images or hosted inference.

Offline review: `.venv/bin/python verify.py`. Independent minimal review environment: Python 3.12, numpy==2.5.4, scipy==1.18.1, scikit-learn==1.9.1 (with their dependencies). Full exact environment in requirements.lock.

PROTOCOL.json and inputs.json were frozen before scoring; model-lock.json pins official model revision and file hashes. raw-responses.jsonl contains every individual call, failures included. analyze.py reproduces saved classifiers and outputs offline. verify.py checks protocol/code/artifacts and scientific integrity without loading inference packages or weights.

Do not rerun freeze.py in this directory. score.py resumes existing call IDs, respects the original absolute deadline, and does not repair or retry responses. No credentials needed. See RUN-COMMANDS.sh after finalization.
