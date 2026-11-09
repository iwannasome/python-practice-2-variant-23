"""Запуск HTTP-сервера или консольных вычислений."""

import argparse
import json
import sys
from pathlib import Path

from practice2.model import Model
from practice2.physics import simulate
from practice2.server import make_server
from practice2.storage import FileStorage


def argument_parser():
    """Описать команды и настройки приложения."""
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    compute = commands.add_parser("compute", help="Вычислить JSON-файл")
    compute.add_argument("input_file", type=Path)
    server = commands.add_parser("server", help="Запустить HTTP API")
    server.add_argument("--host", default="127.0.0.1")
    server.add_argument("--port", type=int, default=8024)
    server.add_argument("--database", type=Path, default=Path("data/db.json"))
    server.add_argument("--backend", choices=("file",), default="file")
    server.add_argument("--test-mode", action="store_true")
    return parser


def serve(args):
    """Открыть хранилище и обслуживать запросы до Ctrl+C."""
    storage = FileStorage(args.database)
    model = Model(storage, test_mode=args.test_mode)
    server = make_server(model, args.host, args.port)
    print(f"HTTP API: http://{args.host}:{server.server_port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        storage.close()


def main():
    """Разобрать команду и вернуть корректный код завершения."""
    args = argument_parser().parse_args()
    try:
        if args.command == "server":
            serve(args)
        else:
            content = args.input_file.read_text(encoding="utf-8")
            print(
                json.dumps(simulate(json.loads(content)), ensure_ascii=False)
            )
    except (OSError, ValueError, OverflowError) as error:
        print(str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
