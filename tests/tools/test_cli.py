"""Tests for the CLI entrypoint."""
import sys
import subprocess
from pathlib import Path

import pytest
import yaml


def _run(args, cwd):
    result = subprocess.run(
        [sys.executable, "tools/generate_automations.py", *args],
        capture_output=True, text=True, cwd=cwd,
    )
    return result


@pytest.fixture
def repo_root():
    return Path(__file__).resolve().parent.parent.parent


def test_cli_writes_to_stdout_when_no_output(make_xlsx, repo_root):
    path = make_xlsx({
        "Dispositivos": [
            ["Area", "Nombre", "Tipo", "entity_id", "Acepta número"],
            ["Sala", "Spots", "light", "light.sala_spots", "dimming %"],
        ],
        "En Casa": [
            [None, "Sala"],
            [None, "Spots"],
            ["19:00", "ON"],
        ],
    })
    result = _run([str(path), "--prefix", "juan"], cwd=repo_root)
    assert result.returncode == 0, result.stderr
    parsed = yaml.safe_load(result.stdout)
    assert len(parsed) == 1
    assert parsed[0]["id"] == "dira_shabat_juan_0001"


def test_cli_writes_to_output_file(make_xlsx, tmp_path, repo_root):
    src = make_xlsx({
        "Dispositivos": [
            ["Area", "Nombre", "Tipo", "entity_id", "Acepta número"],
            ["Sala", "Spots", "light", "light.sala_spots", "dimming %"],
        ],
        "En Casa": [
            [None, "Sala"],
            [None, "Spots"],
            ["19:00", "ON"],
        ],
    })
    out = tmp_path / "out.yaml"
    result = _run(
        [str(src), "--prefix", "juan", "--output", str(out)],
        cwd=repo_root,
    )
    assert result.returncode == 0, result.stderr
    parsed = yaml.safe_load(out.read_text())
    assert parsed[0]["alias"].startswith("[Juan")


def test_cli_exits_nonzero_on_missing_dispositivos(make_xlsx, repo_root):
    path = make_xlsx({"En Casa": [["foo"]]})
    result = _run([str(path), "--prefix", "juan"], cwd=repo_root)
    assert result.returncode != 0
    assert "Dispositivos" in result.stderr


def test_cli_summary_to_stderr(make_xlsx, repo_root):
    path = make_xlsx({
        "Dispositivos": [
            ["Area", "Nombre", "Tipo", "entity_id", "Acepta número"],
            ["Sala", "Spots", "light", "light.sala_spots", "dimming %"],
        ],
        "En Casa": [
            [None, "Sala"],
            [None, "Spots"],
            ["19:00", "ON"],
            ["20:00", "OFF"],
        ],
    })
    result = _run([str(path), "--prefix", "juan"], cwd=repo_root)
    assert result.returncode == 0
    assert "2 automation" in result.stderr.lower() or "2 automations" in result.stderr.lower()
