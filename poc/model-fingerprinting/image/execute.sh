#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
# Smoke must succeed for both exact checkpoints before calibration.
test -f complete-sd14-smoke.json
test -f complete-sd15-smoke.json
for model in sd14 sd15; do
 timeout 1800 .venv/bin/python run.py "$model" calibration > "calibration-$model.log" 2>&1
done
.venv/bin/python freeze.py > freeze.log
sha256sum config.json manifest.json models.json protocol-freeze.json frozen-classifier.json run.py analyze.py > before-heldout.sha256
for model in sd14 sd15; do
 timeout 1800 .venv/bin/python run.py "$model" evaluation > "evaluation-$model.log" 2>&1
done
for model in sd14 sd15; do
 timeout 900 .venv/bin/python run.py "$model" reload > "reload-$model.log" 2>&1
done
.venv/bin/python analyze.py > analysis.log
nvidia-smi > host-after.txt
