"""CLI: convert a Dira Shabat scheduler Excel into HA automations YAML."""
from __future__ import annotations

import argparse
import sys
import warnings as _warnings
from pathlib import Path

# Allow running from repo root without installing the package
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.dira_scheduler.excel_reader import (  # noqa: E402
    DispositivosError,
    read_dispositivos,
    read_schedule_sheet,
)
from tools.dira_scheduler.yaml_emitter import (  # noqa: E402
    build_automations,
    dump_yaml,
)


SHEETS = ("En Casa", "Fuera", "Diario Lun-Vier")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="Path to the client's .xlsx schedule")
    parser.add_argument("--prefix", required=True, help="Client identifier (used in automation ids/aliases)")
    parser.add_argument("--output", help="Write YAML to this file instead of stdout")
    args = parser.parse_args(argv)

    src = Path(args.input)
    if not src.is_file():
        print(f"Error: input file not found: {src}", file=sys.stderr)
        return 2

    try:
        with _warnings.catch_warnings(record=True) as captured:
            _warnings.simplefilter("always")
            devices = read_dispositivos(src)
            cells_by_sheet = {
                sheet: list(read_schedule_sheet(src, sheet)) for sheet in SHEETS
            }
            automations = build_automations(cells_by_sheet, devices, prefix=args.prefix)
    except DispositivosError as err:
        print(f"Error reading Dispositivos: {err}", file=sys.stderr)
        return 1

    yaml_text = dump_yaml(automations)

    if args.output:
        Path(args.output).write_text(yaml_text, encoding="utf-8")
    else:
        # Ensure UTF-8 output on platforms whose default stdout encoding
        # (e.g. Windows cp1252) cannot represent characters used in aliases.
        reconfigure = getattr(sys.stdout, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8")
        sys.stdout.write(yaml_text)

    print(f"Generated {len(automations)} automations.", file=sys.stderr)
    if captured:
        print(f"{len(captured)} warning(s):", file=sys.stderr)
        for w in captured:
            print(f"  - {w.message}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
