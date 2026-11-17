"""Чтение входного JSON-файла и печать SVG в stdout."""

import argparse
import json
import sys
from pathlib import Path

from practice2.barcode import generate

SUCCESS = 0
FAILURE = 1


def main():
    """Разобрать путь к файлу и сообщить об ошибке через stderr."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_file", type=Path)
    args = parser.parse_args()
    try:
        payload = json.loads(args.input_file.read_text(encoding="utf-8"))
        print(generate(payload))
    except (OSError, ValueError, OverflowError) as error:
        print(str(error), file=sys.stderr)
        return FAILURE
    return SUCCESS


if __name__ == "__main__":
    sys.exit(main())
