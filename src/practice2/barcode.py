"""Проверка EAN-13, кодирование модулей и построение SVG."""

from itertools import groupby

LEFT = (
    "0001101",
    "0011001",
    "0010011",
    "0111101",
    "0100011",
    "0110001",
    "0101111",
    "0111011",
    "0110111",
    "0001011",
)
MIXED = (
    "0100111",
    "0110011",
    "0011011",
    "0100001",
    "0011101",
    "0111001",
    "0000101",
    "0010001",
    "0001001",
    "0010111",
)
RIGHT = (
    "1110010",
    "1100110",
    "1101100",
    "1000010",
    "1011100",
    "1001110",
    "1010000",
    "1000100",
    "1001000",
    "1110100",
)
PARITY = (
    "LLLLLL",
    "LLGLGG",
    "LLGGLG",
    "LLGGGL",
    "LGLLGG",
    "LGGLLG",
    "LGGGLL",
    "LGLGLG",
    "LGLGGL",
    "LGGLGL",
)
CODE_LENGTH = 13
DATA_LENGTH = 12
LEFT_QUIET = 11
SYMBOL_WIDTH = 95
SVG_WIDTH = 113
SVG_HEIGHT = 70
BAR_HEIGHT = 58
EVEN_REMAINDER = 0


def complete_ean13(value):
    """Добавить или проверить контрольную цифру GTIN-13."""
    if not isinstance(value, str) or not value.isascii():
        raise ValueError("ean13 должен быть строкой из 12 или 13 цифр")
    if not value.isdigit() or len(value) not in (DATA_LENGTH, CODE_LENGTH):
        raise ValueError("ean13 должен содержать 12 или 13 цифр")
    data = value[:DATA_LENGTH]
    total = sum(
        int(digit) * (1 if index % 2 == EVEN_REMAINDER else 3)
        for index, digit in enumerate(data)
    )
    check = str(-total % 10)
    if len(value) == CODE_LENGTH and value[-1] != check:
        raise ValueError("Неверная контрольная цифра EAN-13")
    return data + check


def encode_modules(value):
    """Преобразовать 13 цифр в 95 светлых и тёмных модулей."""
    digits = complete_ean13(value)
    first = int(digits[0])
    left = "".join(
        (LEFT if parity == "L" else MIXED)[int(digit)]
        for parity, digit in zip(PARITY[first], digits[1:7])
    )
    right = "".join(RIGHT[int(digit)] for digit in digits[7:])
    return "101" + left + "01010" + right + "101"


def render_svg(value):
    """Построить масштабируемый SVG с тихими зонами и подписью."""
    digits = complete_ean13(value)
    bits = encode_modules(digits)
    bars = []
    position = LEFT_QUIET
    for bit, group in groupby(bits):
        width = len(list(group))
        if bit == "1":
            bars.append(
                f'<rect x="{position}" y="0" width="{width}" '
                f'height="{BAR_HEIGHT}"/>'
            )
        position += width
    content = "".join(bars)
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {SVG_WIDTH} {SVG_HEIGHT}" '
        'shape-rendering="crispEdges">'
        f"<title>EAN-13 {digits}</title>{content}"
        f'<text x="{LEFT_QUIET + SYMBOL_WIDTH // 2}" y="68" '
        'text-anchor="middle" font-family="sans-serif" '
        f'font-size="9">{digits}</text></svg>'
    )


def generate(payload):
    """Принять JSON-объект с числом EAN-13 и вернуть SVG."""
    if not isinstance(payload, dict) or set(payload) != {"ean13"}:
        raise ValueError("Ожидается объект JSON с полем ean13")
    return render_svg(payload["ean13"])
