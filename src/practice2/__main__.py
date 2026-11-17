"""Генерация штрих-кода EAN-13 из входного файла."""

import argparse
import json
import sys
from pathlib import Path

from practice2.barcode import generate


def main():
    """Прочитать JSON и напечатать SVG в stdout."""
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    compute = commands.add_parser("compute")
    compute.add_argument("input_file", type=Path)
    args = parser.parse_args()
    try:
        content = args.input_file.read_text(encoding="utf-8")
        print(generate(json.loads(content)))
    except (OSError, ValueError, OverflowError) as error:
        print(str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
