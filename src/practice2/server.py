"""HTTP-сервер на стандартном BaseHTTPRequestHandler."""

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, HTTPServer

from practice2.routes import RouteError, dispatch
from practice2.schema import ConflictError, MissingError

REQUIRED_HEADERS = (("Accept", "text/json"), ("Accept-Language", "ru"))


class ApiHandler(BaseHTTPRequestHandler):
    """Проверять заголовки, маршрутизировать запрос и выдавать JSON."""

    def __getattr__(self, name):
        """Направить любой HTTP-метод через проверку заголовков."""
        if name.startswith("do_"):
            return self.handle_api
        return super().__getattribute__(name)

    def log_message(self, format_string, *args):
        """Не засорять stdout CLI стандартным HTTP-журналом."""

    def do_GET(self):
        """Обслужить чтение одной записи."""
        self.handle_api()

    def do_POST(self):
        """Обслужить выборку записей и построение отчёта."""
        self.handle_api()

    def do_PUT(self):
        """Обслужить создание участника или вычислительного задания."""
        self.handle_api()

    def do_DELETE(self):
        """Отклонить удаление после общей проверки заголовков."""
        self.handle_api()

    def handle_api(self):
        """Проверить заголовки в порядке таблицы и вызвать модель."""
        for name, expected in REQUIRED_HEADERS:
            if self.headers.get(name) != expected:
                self.send_json(
                    HTTPStatus.NOT_ACCEPTABLE,
                    {"error": f"Требуется {name}: {expected}"},
                )
                return
        try:
            result = dispatch(self.server.model, self.command, self.path)
        except RouteError as error:
            self.send_json(error.status, {"error": str(error)})
        except MissingError as error:
            self.send_json(HTTPStatus.NOT_FOUND, {"error": str(error)})
        except ConflictError as error:
            self.send_json(HTTPStatus.CONFLICT, {"error": str(error)})
        except (ValueError, TypeError, UnicodeError) as error:
            self.send_json(HTTPStatus.BAD_REQUEST, {"error": str(error)})
        else:
            self.send_json(HTTPStatus.OK, result)

    def send_json(self, status, value):
        """Отправить UTF-8 JSON с точной длиной тела в байтах."""
        body = json.dumps(value, ensure_ascii=True, allow_nan=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)


def make_server(model, host="127.0.0.1", port=8024):
    """Создать однопоточный сервер с общей моделью и её хранилищем."""
    server = HTTPServer((host, port), ApiHandler)
    server.model = model
    return server
