"""End-to-end fixture test that locks in the YAML output."""
import subprocess
import sys
from pathlib import Path

import yaml


FIXTURES = Path(__file__).parent / "fixtures"


def test_full_fixture_matches_expected(tmp_path):
    src = FIXTURES / "sample_full.xlsx"
    expected = yaml.safe_load((FIXTURES / "sample_full.expected.yaml").read_text())
    out_file = tmp_path / "out.yaml"
    repo_root = Path(__file__).resolve().parent.parent.parent
    result = subprocess.run(
        [
            sys.executable, "tools/generate_automations.py",
            str(src), "--prefix", "sample", "--output", str(out_file),
        ],
        capture_output=True, text=True, cwd=repo_root,
    )
    assert result.returncode == 0, result.stderr
    actual = yaml.safe_load(out_file.read_text())
    assert actual == expected
