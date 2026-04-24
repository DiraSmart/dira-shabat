# Dira Shabat Scheduler — Tools

Generate Home Assistant automations from a per-client Excel schedule.

## Install

```bash
pip install -r tools/requirements.txt
```

## Generate automations

```bash
python tools/generate_automations.py path/to/cliente.xlsx --prefix juan --output juan.yaml
```

See [`docs/specs/2026-04-23-scheduler-design.md`](../docs/specs/2026-04-23-scheduler-design.md) for the Excel format spec.
