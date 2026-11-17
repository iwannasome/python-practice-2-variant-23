# Практика №2, вариант 23 — этап 1

Вычислительная задача по теме курсовой: генерация штрих-кода EAN-13 в SVG.
Вход — JSON-файл с полем `ean13`, результат печатается в stdout.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m pip install --no-deps -e .
./run.sh compute examples/case_1.json
.venv/bin/python -m pytest tests/test_barcode.py -q
```

Четыре примера находятся в каталоге `examples/`.
