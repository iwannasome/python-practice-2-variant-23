# Практическая работа 2 Вариант 23

Сысоев Даниил Денисович, ИКБО-71-24. РТУ МИРЭА, 2026.  
Дисциплина: «Прикладная разработка серверных частей веб-приложений
на языке Питон». Преподаватель: Горчаков Артём Владимирович.

Публичный репозиторий: [python-practice-2-variant-23](https://github.com/iwannasome/python-practice-2-variant-23).

Основание: сборник индивидуальных вариантов практического задания №2,
ИКБО-71-24, страницы 4–5, 83–86, рисунок и таблица 23.

Проект принимает вычислительные задания по HTTP, запускает консольную
утилиту через `subprocess`, сохраняет участников, задания и ответы на диск.
Этап 2 использует собственное JSON-хранилище, этап 3 — библиотеку TinyDB.
Модель, HTTP-маршруты, API-клиент и независимый эталон MBT общие.

## Установка и запуск в Ubuntu

Требуется Python 3.11+ и пакет `python3-venv`.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m pip install --no-deps -e .
./run.sh compute examples/case_1.json
./run.sh server --backend tinydb --database data/tinydb.json
```

Завершение сервера: Ctrl+C. Данные остаются на диске.
Для этапа 2 используется отдельный файл:

```sh
./run.sh server --backend file --database data/file.json
```

Форматы хранилищ не следует смешивать в одном файле при экспериментах.
Один файл открывается одним процессом сервера. Модель использует RLock,
а HTTPServer последовательно обслуживает запросы. Задание выполняется
синхронно: PUT завершается после сохранения результата.

Тестовый режим сохраняет Task и Response без вызова `subprocess`:

```sh
./run.sh server --test-mode --database data/test.json
```

У тестового Response: `status="test"`, `response='{"test_mode": true}'`,
`failure=""`, `duration=0`. Это явная заглушка результата вычисления.

## Этап 1 Вычислительная утилита

Вычислительная часть — вертикальное движение независимых шариков до
первого касания пола. Модель использует метры, секунды и м/с; направление
вверх положительно. Сопротивление воздуха, отскоки и столкновения шариков
не моделируются. После касания пола высота и скорость равны нулю.

Входной JSON-файл содержит:

- `time`: конечное неотрицательное число, момент наблюдения в секундах;
- `gravity`: конечное положительное число, по умолчанию 9.81 м/с²;
- `balls`: непустой список объектов с `height` и необязательной `velocity`;
- `height`: конечная неотрицательная начальная высота;
- `velocity`: конечная начальная скорость, по умолчанию 0.

Логические значения не принимаются как числа. Некорректный JSON, файл
или физический параметр дают ненулевой код завершения и сообщение в stderr.
Результат успешного вычисления — один JSON в stdout.

До касания пола:

```text
y(t) = h0 + v0*t - g*t²/2
v(t) = v0 - g*t
t_impact = (v0 + sqrt(v0² + 2*g*h0)) / g
```

Для каждого шарика возвращаются `height`, `velocity`, `impact_time`,
`state` (`airborne` или `landed`). Числа округляются до 8 знаков после
запятой; размерности результата соответствуют входным данным.

Четыре обязательных примера находятся в `examples/`:

| Файл | h0 | v0 | t | Высота | Скорость | Состояние |
|---|---:|---:|---:|---:|---:|---|
| case_1.json | 20 | 0 | 1 | 15.095 | -9.81 | airborne |
| case_2.json | 0 | 10 | 1 | 5.095 | 0.19 | airborne |
| case_3.json | 10 | 0 | 3 | 0 | 0 | landed |
| case_4.json | 5 | -2 | 0.5 | 2.77375 | -6.905 | airborne |

```sh
./run.sh compute examples/case_1.json
./run.sh compute examples/case_2.json
./run.sh compute examples/case_3.json
./run.sh compute examples/case_4.json
```

Самостоятельный интерфейс утилиты, который вызывает сервер:

```sh
.venv/bin/python -m practice2.cli examples/case_1.json
```

## Этап 2 HTTP API

Обработчик наследует `http.server.BaseHTTPRequestHandler`.
Название `BaseHttpRequestHandler` в сборнике трактуется как этот класс
стандартной библиотеки Python. FastAPI в варианте 23 не требуется.

Каждый запрос содержит `Accept: text/json` и `Accept-Language: ru`.
Заголовки проверяются именно в этом порядке. Отсутствующее или неверное
значение даёт 406 с JSON-сообщением о первом нарушении.
Корректная операция возвращает 200. Тело ответа имеет тип
`application/json; charset=utf-8`; длина задаётся в байтах.

| № | Метод | Путь | Параметры query | Метод модели и клиента |
|---|---|---|---|---|
| 1.1 | PUT | /api/save/member/:uid | поля Member | save_member(uid, values) |
| 1.2 | POST | /api/collect/member | фильтры Member | collect_member(filters=None) |
| 1.3 | GET | /api/read/member | uid | read_member(uid) |
| 2.1 | PUT | /api/save/task/:uid | поля Task | save_task(uid, values) |
| 2.2 | POST | /api/collect/task/:member | фильтры Task | collect_task(member, filters=None) |
| 2.3 | GET | /api/read/task | uid | read_task(uid) |
| 3.1 | POST | /api/collect/response/:task | фильтры Response | collect_response(task, filters=None) |
| 3.2 | GET | /api/read/response | uid | read_response(uid) |
| 4.1 | POST | /api/collect/report | нет | collect_report() |

Все входные данные передаются в пути и query, тела запросов не используются.
Незаполненный фильтр возвращает все подходящие записи; несколько полей
фильтра соединяются логическим AND. Сравнение точное, с учётом типа.
Коллекции сортируются по uid, отсутствующая коллекция — пустой список.
Параметр пути `member` или `task` задаёт обязательную область поиска.

Дополнительные ошибочные ситуации: 400 — неверные параметры,
404 — отсутствующая запись или маршрут, 405 — неверный метод,
409 — повторный первичный ключ. Повторяющиеся query-параметры и
неизвестные поля отклоняются. Ошибка вычисления сохраняется в Response
со `status="error"`; корректно принятое задание остаётся успешной
операцией API с кодом 200.

### Схема данных

| Сущность | Поля и типы |
|---|---|
| Member | uid:int, datetime:int, ip:str, locale:str |
| Task | uid:int, datetime:int, input:str, member:int, tags:str, completed:int, launched:int |
| Response | uid:int, datetime:int, response:str, status:str, failure:str, task:int, duration:int |

UID — положительный целый ключ, уникальный внутри своей таблицы.
Task.member ссылается на существующего Member, Response.task — на Task.
IP и локаль сохраняются строками, дополнительные ограничения формата
схемой задания не вводятся. Времена — целые Unix-секунды.

При создании Member обязательных полей кроме uid нет: datetime по умолчанию
равен текущему времени, ip пустой, locale `ru`. Для Task обязательны
`member` и `input`; tags по умолчанию пустой. Необязательный datetime можно
задать явно. `launched` и `completed` сервер устанавливает по времени
начала и окончания вычисления. Они имеют тип int, как в ER-схеме.

Task.input содержит JSON-текст входного файла. Сервер записывает его во
временный файл, вызывает `sys.executable -m practice2.cli <file>` через
`subprocess.run` и удаляет временный каталог. Оболочка не запускается.
Тайм-аут процесса 10 секунд. Успешный stdout становится Response.response,
stderr сохраняется в failure. duration измеряется в целых миллисекундах
монотонными часами. Время создания Response берётся после вычисления.

На каждое новое задание автоматически создаётся один Response с тем же uid
и ссылкой task на задание. Публичного маршрута создания Response в задании
нет; изменение и удаление записей в таблице 23 также не предусмотрены.

### Пример запросов

Сервер должен работать в отдельном терминале.

```sh
curl -X PUT 'http://127.0.0.1:8024/api/save/member/1?ip=127.0.0.1&locale=ru' \
  -H 'Accept: text/json' -H 'Accept-Language: ru'

curl -X PUT 'http://127.0.0.1:8024/api/save/task/1' --get \
  --data-urlencode 'member=1' --data-urlencode 'tags=fall' \
  --data-urlencode 'input={"time":1,"balls":[{"height":20}]}' \
  -H 'Accept: text/json' -H 'Accept-Language: ru'

curl 'http://127.0.0.1:8024/api/read/response?uid=1' \
  -H 'Accept: text/json' -H 'Accept-Language: ru'

curl -X POST 'http://127.0.0.1:8024/api/collect/report' \
  -H 'Accept: text/json' -H 'Accept-Language: ru'
```

Пример через класс клиента:

```python
import json

from practice2.client import ApiClient

client = ApiClient()
client.save_member(2, {"ip": "::1", "locale": "ru"})
client.save_task(2, {
    "member": 2,
    "input": json.dumps({"time": 3, "balls": [{"height": 10}]}),
    "tags": "fall",
})
print(client.read_response(2))
print(client.collect_report())
```

`ApiClient.request(method, path, params=None, headers=None)` позволяет
проверить ошибочные запросы. `headers=None` включает обязательные
заголовки, `{}` отправляет запрос без них. ApiError содержит `status` и
`payload`; сетевые ошибки остаются стандартными исключениями urllib.

### Формула отчёта

Результат — множество уникальных троек `[Member.ip, Response.duration,
Task.tags]`. Используется строгое условие `Response.datetime > now - 540`:
ответ ровно 9 минут назад исключается. Верхнего ограничения `<= now`
в формуле нет, поэтому ответ с будущим временем включается.

Модель обходит Response, присоединяет Task по `task` и Member по `member`.
При соблюдении внешних ключей это эквивалентно правому соединению T и R
с последующим внутренним соединением с M в формуле 23.
Множество удаляет дубликаты проекции; результат сортируется.

## Этап 3 TinyDB

`TinyStorage` использует именно библиотеку `tinydb`, её JSONStorage,
документные таблицы и `Query().uid`. Три операции адаптера совпадают с
FileStorage: `all(entity)`, `write(entity, row)`, `close()`.
Внедрение адаптера в Model заменяет слой хранения без переписывания API.
`FileStorage.write` использует временный файл, fsync и os.replace;
`TinyStorage.write` — upsert документа по прикладному uid.

## Тестирование и отдельное покрытие MBT

```sh
make lint
make test
make mbt-file
make mbt-tiny
```

`tests/mbt_machine.py` реализует RuleBasedStateMachine. Через настоящий
ApiClient выполняются генерируемые действия: создание, чтение, поиск,
фильтрация, дубликаты, неверные ссылки, неверные запросы и заголовки,
изменение тестовых часов и перезапуск сервера с повторным открытием БД.
Инвариант сопоставляет ответы с независимыми Python-словарями. Эталон
отчёта использует прямое тройное соединение, не вызывает Model и storage.

Инициализация использует генерируемые строки и создаёт дубликат проекции.
В каждом сценарии проверяются обе стороны границы 540 секунд и будущее
время. После этого Hypothesis выбирает последующие правила и данные.
Настройки: max_examples=25, stateful_step_count=25, deadline=None,
derandomize=True. Эти пределы не означают ровно 625 исполненных действий.

Для этапа 3 наследуется та же машина; заменяется только адаптер хранилища.
Тесты обычного набора не подмешиваются в отдельные измерения MBT:

```sh
.venv/bin/python -m coverage run --branch --data-file=.coverage.file \
  -m pytest tests/test_mbt_file.py -q
.venv/bin/python -m coverage json --data-file=.coverage.file \
  -o coverage-file.json
.venv/bin/python tests/check_mbt_coverage.py coverage-file.json
```

Аналогично для `tests/test_mbt_tiny.py` и `.coverage.tiny`.
`make mbt-file` и `make mbt-tiny` также строят HTML-отчёты
`htmlcov-file/index.html`, `htmlcov-tiny/index.html`.

Автоматический контроль требует 100% строк и ветвей `model.py`,
`routes.py`, `server.py`, `client.py` в каждом отдельном MBT-прогоне.
Общий процент проекта ниже: MBT работает в тестовом режиме и не должен
запускать CLI, физику или основной цикл сервера из командной строки.
Неиспользуемый альтернативный адаптер также остаётся в полном отчёте.
Ничего не исключено из измерения для повышения процента.

## Строгие правила оформления

`make lint` запускает pycodestyle, Ruff, Ruff Formatter, flake8 с
pep8-naming и независимый AST/tokenize-аудит всего кода src и tests.
Проверяются строки до 79 символов, docstring до 72, 4 пробела отступа,
имена PEP 8, порядок импортов, сложность до 10, файлы до 1000 строк,
функции до 40 строк, до 7 аргументов без self/cls, отсутствие обычных
комментариев и числовых литералов в сравнениях.

Сохранены только необходимые исключения: W503 не используется как правило
стиля, а do_GET/do_POST/do_PUT/do_DELETE сохраняют имена протокола
BaseHTTPRequestHandler. Проверка имён для остального кода включена.
Объяснения в Python оформлены docstring. Этапы разработки сохранены
отдельными Conventional Commits; проверить их можно через `git log --oneline`.

## Структура и функции

| Модуль | Ответственность и функции |
|---|---|
| physics.py | number: проверка числа; ball_at_time: состояние шарика; simulate: обработка задачи |
| cli.py | main: входной файл, JSON в stdout, ошибки в stderr |
| __main__.py | argument_parser: CLI-настройки; serve: жизненный цикл сервера; main: выбор команды |
| schema.py | uid_value: ключ; validate: типы и поля; defaults: значения по умолчанию |
| model.py | девять публичных методов из таблицы API; _new, _read, _collect: общая проверка и выборка |
| routes.py | parse_values: query; resolve: путь и метод; dispatch: вызов модели |
| server.py | make_server; ApiHandler.do_GET/do_POST/do_PUT/do_DELETE; handle_api; send_json; log_message |
| client.py | девять методов модели; request: HTTP; ApiError: код и сообщение ошибки |
| runner.py | execute: test/real; run_process: subprocess и обработка тайм-аута |
| storage.py | FileStorage: __init__, all, write, close |
| tiny_storage.py | TinyStorage: __init__, all, write, close |
| tests/ | интеграционные тесты, одна общая машина MBT, аудит и проверка покрытия |

Docstring рядом с каждой функцией описывает её назначение.

## Настройки и сборка

| Настройка | Значение по умолчанию | Где задаётся |
|---|---|---|
| Адрес сервера | 127.0.0.1 | --host |
| Порт | 8024 | --port |
| База данных | data/db.json | --database |
| Адаптер | tinydb | --backend file или tinydb |
| Тестовый режим | выключен | --test-mode |
| Интерпретатор run.sh | .venv/bin/python | переменная PYTHON |
| URL клиента | http://127.0.0.1:8024 | ApiClient(base_url=...) |
| Тайм-аут клиента | 15 секунд | ApiClient(timeout=...) |
| Тайм-аут subprocess | 10 секунд | runner.TIMEOUT_SECONDS |
| Окно отчёта | 540 секунд | schema.WINDOW_SECONDS |
| Часы модели | time.time | Model(clock=...) |
| Ускорение по умолчанию | 9.81 м/с² | вход gravity / physics.DEFAULT_GRAVITY |

Python-код не требует отдельной компиляции. Проверка синтаксиса и wheel:

```sh
.venv/bin/python -m compileall -q src
make build
```

Установка wheel: `.venv/bin/python -m pip install dist/*.whl`.
В git не включаются виртуальное окружение, кеши, БД, coverage, wheel,
PDF/DOCX, архивы и настройки редактора. Отчёт и архив комплекта находятся
снаружи исходного репозитория. Файл `.github/workflows/check.yml`
повторяет линтеры, тесты и два отдельных измерения MBT при push/PR.

## Источники

- Сборник задания №2 ИКБО-71-24: с. 4–5, 83–86.
- [Python http.server](https://docs.python.org/3/library/http.server.html).
- [Python subprocess](https://docs.python.org/3/library/subprocess.html).
- [Hypothesis Stateful testing](https://hypothesis.readthedocs.io/en/latest/stateful.html).
- [coverage.py Branch coverage](https://coverage.readthedocs.io/en/latest/branch.html).
- [TinyDB Usage](https://tinydb.readthedocs.io/en/latest/usage.html).
- [PEP 8](https://peps.python.org/pep-0008/).
