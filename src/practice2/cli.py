"""Чтение входного JSON-файла и печать вычисленного JSON в stdout."""

import argparse
import json
import sys
from pathlib import Path

from practice2.physics import simulate

SUCCESS = 0
FAILURE = 1


def main():
    """Разобрать путь к файлу и сообщить об ошибке через stderr."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_file", type=Path)
    args = parser.parse_args()
    try:
        payload = json.loads(args.input_file.read_text(encoding="utf-8"))
        result = simulate(payload)
        print(json.dumps(result, ensure_ascii=False, allow_nan=False))
    except (OSError, ValueError, OverflowError) as error:
        print(str(error), file=sys.stderr)
        return FAILURE
    return SUCCESS


if __name__ == "__main__":
    sys.exit(main())
