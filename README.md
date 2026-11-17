# Практическая работа №2, вариант 23

Сысоев Даниил Денисович, ИКБО-71-24. РТУ МИРЭА, 2026.
Дисциплина: «Прикладная разработка серверных частей веб-приложений
на языке Питон». Преподаватель: Горчаков Артём Владимирович.

Тема вычислительной задачи: **веб-приложение с HTTP API для асинхронной
генерации штрих-кодов EAN-13 в формате SVG**.

[Инструкция по пяти вопросам с фото](docs/ЗАЩИТА_ПО_ФОТО.md) и
[готовые материалы для сдачи](submission/README.md) находятся в репозитории.

Публичный репозиторий:
https://github.com/iwannasome/python-practice-2-variant-23

Основание: сборник индивидуальных вариантов практического задания №2,
ИКБО-71-24, вариант 23, с. 83–86. Этап 1 принимает входной файл и
печатает SVG; этап 2 принимает задания через HTTP и запускает CLI
через subprocess; этап 3 заменяет собственное файловое хранилище
на TinyDB. Девять маршрутов и формула отчёта соответствуют таблице 23.

## Установка

Нужны Python 3.11+ и python3-venv.

~~~
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m pip install --no-deps -e .
~~~

## Этап 1: EAN-13 → SVG в командной строке

Вход — JSON-объект с единственным полем ean13. Значение — строка
из 12 цифр (контрольная цифра рассчитывается) или из 13 цифр
(контрольная цифра проверяется). Строковый тип сохраняет ведущие нули.
Любая иная длина, недесятичный символ или неверная контрольная цифра
отклоняются с сообщением в stderr и ненулевым кодом завершения.

Для первых 12 цифр веса справа чередуются 3 и 1; контрольная цифра
дополняет взвешенную сумму до кратного 10. Первая цифра задаёт
чередование левых наборов A/B (в коде LEFT/MIXED), справа используется
набор C (RIGHT). Охранные последовательности: 101, 01010, 101.
Итог содержит 95 модулей, левую тихую зону 11 модулей и правую
7 модулей. SVG состоит из полос rect и подписи EAN-13. Наличие
правильной контрольной цифры не подтверждает регистрацию номера в GS1.

Четыре входных примера находятся в examples/:

| Файл | Исходное значение | Смысл |
| --- | --- | --- |
| case_1.json | 590123412345 | вычисление контрольной цифры |
| case_2.json | 4006381333931 | проверка готового EAN-13 |
| case_3.json | 000000000000 | сохранение ведущих нулей |
| case_4.json | 978030640615 | другое значение первой цифры |

~~~
./run.sh compute examples/case_1.json
./run.sh compute examples/case_2.json
./run.sh compute examples/case_3.json
./run.sh compute examples/case_4.json
~~~

Команда compute выводит только SVG в stdout. Запустить отдельную
CLI-утилиту, которую вызывает сервер, можно так:

~~~
.venv/bin/python -m practice2.cli examples/case_1.json
mkdir -p data
./run.sh compute examples/case_1.json > data/case_1.svg
~~~

Функция complete_ean13 проверяет и дополняет номер,
encode_modules создаёт 95-битный рисунок, render_svg строит SVG,
generate проверяет структуру JSON.

## Этап 2: HTTP API и асинхронное выполнение

Сервер основан на стандартном BaseHTTPRequestHandler.
Все входные поля передаются через путь и строку запроса, а не тело.
Для любого метода обязательны Accept: text/json и Accept-Language: ru
именно в этом порядке. Нарушение первого найденного заголовка даёт
406 и JSON-сообщение. Успешная операция возвращает 200 и JSON.

| № | Метод | Маршрут | Метод клиента и модели |
| --- | --- | --- | --- |
| 1.1 | PUT | /api/save/member/:uid | save_member |
| 1.2 | POST | /api/collect/member | collect_member |
| 1.3 | GET | /api/read/member | read_member |
| 2.1 | PUT | /api/save/task/:uid | save_task |
| 2.2 | POST | /api/collect/task/:member | collect_task |
| 2.3 | GET | /api/read/task | read_task |
| 3.1 | POST | /api/collect/response/:task | collect_response |
| 3.2 | GET | /api/read/response | read_response |
| 4.1 | POST | /api/collect/report | collect_report |

Схема Member: uid:int, datetime:int, ip:str, locale:str.
Схема Task: uid:int, datetime:int, input:str, member:int, tags:str,
completed:int, launched:int.
Схема Response: uid:int, datetime:int, response:str, status:str,
failure:str, task:int, duration:int. Время — Unix-секунды,
duration — целые миллисекунды. UID положителен и уникален в таблице.
Task.member и Response.task — внешние ссылки.

Task.input содержит JSON-текст, например строку
{"ean13": "590123412345"}. При PUT 2.1 сервер сохраняет Task
и Response со status="pending", затем немедленно возвращает Task.
Фоновый исполнитель записывает вход во временный файл и запускает
sys.executable -m practice2.cli <file> через subprocess без shell.
После окончания он записывает SVG в Response.response, status="success"
и время завершения в Task.completed. Ошибка CLI даёт status="error"
и текст в failure. Следовательно, read_response может сначала вернуть
pending, а затем success/error. Продолжительность ограничена
10 секундами для дочернего процесса. При остановке сервера он ждёт
уже принятые фоновые задачи и закрывает БД.

Тестовый режим не запускает subprocess и сразу сохраняет Response
со status="test", response='{"test_mode": true}' и duration=0.
Он нужен для детерминированного MBT.

Для этапа 2:

~~~
./run.sh server --backend file --database data/file.json
~~~

Для этапа 3:

~~~
./run.sh server --backend tinydb --database data/tinydb.json
~~~

По умолчанию сервер слушает 127.0.0.1:8024. Остановить: Ctrl+C.
Не смешивайте форматы FileStorage и TinyDB в одном файле.
Параметры: --host, --port, --database, --backend, --test-mode.

Пример запросов из второго терминала; --noproxy исключает локальный
сервер из системного прокси:

~~~
curl --noproxy '*' -sS -X PUT \
  'http://127.0.0.1:8024/api/save/member/1?ip=127.0.0.1&locale=ru' \
  -H 'Accept: text/json' -H 'Accept-Language: ru'

curl --noproxy '*' -sS -X PUT \
  'http://127.0.0.1:8024/api/save/task/1' --get \
  --data-urlencode 'member=1' \
  --data-urlencode 'tags=ean13' \
  --data-urlencode 'input={"ean13":"590123412345"}' \
  -H 'Accept: text/json' -H 'Accept-Language: ru'

curl --noproxy '*' -sS \
  'http://127.0.0.1:8024/api/read/response?uid=1' \
  -H 'Accept: text/json' -H 'Accept-Language: ru'

curl --noproxy '*' -sS -X POST \
  'http://127.0.0.1:8024/api/collect/report' \
  -H 'Accept: text/json' -H 'Accept-Language: ru'
~~~

Повторяйте read_response до смены pending. Для нового показа берите
новую БД или новые UID. Неизвестные поля, повторяющиеся параметры
и плохие типы дают 400; отсутствие записи — 404; неверный метод —
405; повторный ключ — 409.

ApiClient имеет те же девять имён методов, что и Model.
ApiClient.request позволяет проверить ошибки и заголовки напрямую.

## Формула отчёта 23

collect_report строит множество уникальных троек
[Member.ip, Response.duration, Task.tags]. Соединения выполняются
по Task.member = Member.uid и Response.task = Task.uid.
Строгое условие Response.datetime > now - 540 исключает ответ
ровно девять минут назад. Результат отсортирован. Формула не
фильтрует status, поэтому ожидающий Response тоже участвует
с текущим duration=0. В тестовом режиме часы управляемы.

## Этап 3: TinyDB

FileStorage хранит три таблицы в собственном JSON-файле и заменяет
его атомарно. TinyStorage использует библиотеку tinydb, её JSONStorage,
таблицы и поиск по Query().uid. Оба адаптера имеют all, write, close.
Модель, клиент и маршруты при замене адаптера не меняются.
Файл data/tinydb.json можно открыть как обычный JSON после записи.
Один файл БД обслуживается одним процессом сервера.

## Проверки и сборка

~~~
make lint
make test
make mbt-file
make mbt-tiny
make build
~~~

make lint проверяет pycodestyle, Ruff, Ruff Formatter, flake8,
pep8-naming и собственный аудит: строки не длиннее 79 символов,
функции не длиннее 40 строк, не более 7 аргументов, сложность
не выше 10, без обычных комментариев и магических чисел в сравнениях.
Имена do_GET/do_POST/do_PUT/do_DELETE обязательны по протоколу
BaseHTTPRequestHandler и являются единственным исключением именования.

tests/mbt_machine.py — RuleBasedStateMachine с независимыми словарями
Member, Task и Response. Она через реальный HTTP-клиент проверяет
девять маршрутов, ошибки, фильтрацию, дубликаты, перезапуск БД,
границу 540 секунд и формулу отчёта. Для двух адаптеров идут
раздельные прогоны. tests/check_mbt_coverage.py требует 100% строк
и ветвей client.py, model.py, routes.py, server.py и все девять
маршрутов в каждом MBT-прогоне. Общий процент ниже, потому что
тестовый режим не запускает CLI, генератор штрих-кода и фоновый
исполнитель. Ничто не исключено из измерения ради процента.

Синтаксис можно проверить через
.venv/bin/python -m compileall -q src. Сборка создаёт wheel в dist/.
В репозиторий не входят виртуальное окружение, БД, coverage,
сборочные артефакты, PDF/DOCX и архивы. История изменений оформлена
Conventional/Scoped Commits. CI повторяет основные проверки.

## Где что находится

| Файл | Назначение |
| --- | --- |
| src/practice2/barcode.py | цифра, модули, SVG |
| src/practice2/cli.py | отдельная CLI-утилита для subprocess |
| src/practice2/__main__.py | команды compute и server |
| src/practice2/runner.py | subprocess и фоновые задания |
| src/practice2/server.py | заголовки и HTTP-ответы |
| src/practice2/routes.py | таблица 23 и маршрутизация |
| src/practice2/model.py | девять операций и отчёт |
| src/practice2/client.py | HTTP-клиент с девятью методами |
| src/practice2/schema.py | поля и проверка типов |
| src/practice2/storage.py | файловая БД этапа 2 |
| src/practice2/tiny_storage.py | TinyDB этапа 3 |
| tests/ | обычные и модельные тесты |

## Источники

- Сборник задания №2 ИКБО-71-24, с. 83–86.
- GS1 General Specifications: https://ref.gs1.org/standards/genspecs/
- Python http.server: https://docs.python.org/3/library/http.server.html
- Python subprocess: https://docs.python.org/3/library/subprocess.html
- Hypothesis Stateful: https://hypothesis.readthedocs.io/en/latest/stateful.html
- coverage.py: https://coverage.readthedocs.io/en/latest/branch.html
- TinyDB: https://tinydb.readthedocs.io/en/latest/usage.html
