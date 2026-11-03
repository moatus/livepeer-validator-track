# Recorded experiment commands, run from /home/smart/repos/livepeer.
# This is an audit transcript, not an instruction to overwrite completed results.
uv venv research/judge-score-fingerprinting-poc/2026-10-25/.venv
uv pip install --python research/judge-score-fingerprinting-poc/2026-10-25/.venv/bin/python -r research/image-fingerprinting-poc/2026-10-25/requirements.lock scikit-learn
research/judge-score-fingerprinting-poc/2026-10-25/.venv/bin/python research/judge-score-fingerprinting-poc/2026-10-25/prepare.py
research/judge-score-fingerprinting-poc/2026-10-25/.venv/bin/python research/judge-score-fingerprinting-poc/2026-10-25/download.py
research/judge-score-fingerprinting-poc/2026-10-25/.venv/bin/python research/judge-score-fingerprinting-poc/2026-10-25/generate.py sd14
research/judge-score-fingerprinting-poc/2026-10-25/.venv/bin/python research/judge-score-fingerprinting-poc/2026-10-25/generate.py sd15
research/judge-score-fingerprinting-poc/2026-10-25/.venv/bin/python research/judge-score-fingerprinting-poc/2026-10-25/generate.py sdxl
research/judge-score-fingerprinting-poc/2026-10-25/.venv/bin/python research/judge-score-fingerprinting-poc/2026-10-25/score_local.py
research/judge-score-fingerprinting-poc/2026-10-25/.venv/bin/python research/judge-score-fingerprinting-poc/2026-10-25/analyze.py
research/judge-score-fingerprinting-poc/2026-10-25/.venv/bin/python research/judge-score-fingerprinting-poc/2026-10-25/plot.py
research/judge-score-fingerprinting-poc/2026-10-25/.venv/bin/python research/judge-score-fingerprinting-poc/2026-10-25/write_report.py
research/judge-score-fingerprinting-poc/2026-10-25/.venv/bin/python research/judge-score-fingerprinting-poc/2026-10-25/verify.py
