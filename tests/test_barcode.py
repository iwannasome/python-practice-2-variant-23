"""Проверки кодирования EAN-13 и вывода SVG."""

import subprocess
import sys
from xml.etree import ElementTree

import pytest

from practice2.barcode import complete_ean13, encode_modules, render_svg

SVG_NS = "http://www.w3.org/2000/svg"


@pytest.mark.parametrize(
    "source,expected",
    [
        ("590123412345", "5901234123457"),
        ("4006381333931", "4006381333931"),
        ("000000000000", "0000000000000"),
    ],
)
def test_check_digit(source, expected):
    """Контрольная цифра соответствует известным примерам EAN-13."""
    assert complete_ean13(source) == expected


@pytest.mark.parametrize(
    "source", ["", "123", "12345678901234", "12345678901x", "4006381333932"]
)
def test_invalid_code(source):
    """Отклонить длину, символы и неверную контрольную цифру."""
    with pytest.raises(ValueError):
        complete_ean13(source)


def test_module_structure():
    """EAN-13 содержит 95 модулей и три охранных шаблона."""
    bits = encode_modules("0000000000000")
    assert bits == "101" + "0001101" * 6 + "01010" + "1110010" * 6 + "101"


def test_svg_contains_bars():
    """SVG остаётся XML и содержит полосы без потери модулей."""
    svg = render_svg("4006381333931")
    root = ElementTree.fromstring(svg)
    assert root.tag == f"{{{SVG_NS}}}svg"
    assert root.attrib["viewBox"] == "0 0 113 70"
    bars = root.findall(f"{{{SVG_NS}}}rect")
    assert bars
    assert sum(int(bar.attrib["width"]) for bar in bars) == (
        encode_modules("4006381333931").count("1")
    )


def test_barcode_cli(tmp_path):
    """CLI принимает JSON-файл и выдаёт готовый SVG в stdout."""
    source = tmp_path / "input.json"
    source.write_text('{"ean13": "590123412345"}')
    result = subprocess.run(
        [sys.executable, "-m", "practice2.cli", str(source)],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "5901234123457" in result.stdout
    assert ElementTree.fromstring(result.stdout).tag == f"{{{SVG_NS}}}svg"
    assert result.stderr == ""


def test_cli_invalid_code(tmp_path):
    """Некорректный EAN-13 даёт stderr и ненулевой код завершения."""
    source = tmp_path / "invalid.json"
    source.write_text('{"ean13": "4006381333932"}')
    result = subprocess.run(
        [sys.executable, "-m", "practice2.cli", str(source)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode
    assert result.stdout == ""
    assert result.stderr
