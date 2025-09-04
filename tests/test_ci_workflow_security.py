from pathlib import Path

import yaml


def test_ci_workflow_has_security_steps():
    ci = yaml.safe_load(Path('.github/workflows/ci.yml').read_text())
    steps = []
    for job in ci.get('jobs', {}).values():
        for step in job.get('steps', []):
            run = step.get('run')
            if isinstance(run, str):
                steps.append(run)
    assert any('poetry update' in s for s in steps)
    assert any('bandit' in s for s in steps)

