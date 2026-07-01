#!/usr/bin/env python3
from __future__ import annotations
import json
import sys
from pathlib import Path

results_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('results')
artifact = results_dir / 'C_01_result.json'
rubrics = []
passed = 0
for idx in range(1, 11):
    rubric_id = 'C_01_R' + str(idx).zfill(2)
    ok = artifact.exists()
    evidence = str(artifact) if ok else 'missing primary result artifact'
    if ok:
        try:
            data = json.loads(artifact.read_text(encoding='utf-8'))
            ok = all(key in data for key in ['status', 'task_id', 'summary', 'findings', 'evidence', 'limitations'])
            evidence = 'required fields present' if ok else 'required fields missing'
        except Exception as exc:
            ok = False
            evidence = 'invalid JSON: ' + str(exc)
    if ok:
        passed += 1
    rubrics.append({'rubric_id': rubric_id, 'passed': ok, 'score': 1 if ok else 0, 'reason': evidence, 'evidence': evidence})
result = {'status': 'pass' if passed >= 8 else 'fail', 'passed_checks': passed, 'failed_checks': 10 - passed, 'total_checks': 10, 'rubrics': rubrics}
Path('grading_result.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
