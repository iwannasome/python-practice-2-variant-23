# Практика №2, вариант 23 — этапы 1–2

Тема: асинхронная генерация штрих-кодов EAN-13 в SVG через HTTP API.
Первый этап принимает JSON-файл через CLI и печатает SVG в stdout.
Второй этап запускает CLI из фонового subprocess и сохраняет результаты
в собственной файловой JSON-базе. HTTP API содержит девять маршрутов
для Member, Task, Response и отчёта по варианту 23.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m pip install --no-deps -e .
./run.sh compute examples/case_1.json
./run.sh server --backend file --database data/file.json
make lint
make test
make mbt-file
```

Параметры сервера: `--host`, `--port`, `--database`, `--test-mode`.
Для всех запросов обязательны `Accept: text/json` и `Accept-Language: ru`.
В MBT используются независимая модель и настоящий HTTP-клиент.
