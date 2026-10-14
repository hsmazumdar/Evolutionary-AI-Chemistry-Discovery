#!/usr/bin/env bash
# Regenerate every V05 table and figure. FULL=1 re-runs all experiments (~30-60 min on 8 cores); default reuses results/.
set -euo pipefail; cd "$(dirname "$0")/.."; PY=${PY:-python}; XPY=${XPY:-/workspace/venv_v05x/bin/python}
if [ "${FULL:-0}" = "1" ]; then
  $PY scripts/build_dataset.py            # needs V03 MP snapshot (see V05_DATASET_AUDIT.md)
  $PY scripts/run_h1_discovery.py; $PY scripts/run_h2_transfer.py; $PY scripts/run_h3_memory.py
  $PY phase8/run_regression_benchmark.py --xpy "$XPY"; $PY scripts/run_exploratory.py; $PY scripts/run_industrial_case.py
fi
$PY scripts/dataset_qc.py > /dev/null; $PY scripts/run_statistics.py > /dev/null; $PY scripts/make_figures.py; $PY -m pytest -q tests
