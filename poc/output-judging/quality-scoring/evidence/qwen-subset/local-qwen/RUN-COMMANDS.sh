#!/bin/bash
# Working directory: this artifact directory. Downloads require public network only.
# All inference is local. Existing ledgers are resumed.
.venv/bin/python setup.py
.venv/bin/python freeze.py # intentionally refuses if already frozen
.venv/bin/python score.py
.venv/bin/python analyze.py
.venv/bin/python write_report.py
.venv/bin/python verify.py
