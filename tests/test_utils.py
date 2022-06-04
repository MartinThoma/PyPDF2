import io
import os

import pytest

import PyPDF2._utils
from PyPDF2.errors import PdfStreamError

TESTS_ROOT = os.path.abspath(os.path.dirname(__file__))
PROJECT_ROOT = os.path.dirname(TESTS_ROOT)
RESOURCE_ROOT = os.path.join(PROJECT_ROOT, "resources")


@pytest.mark.parametrize(
    ("stream", "expected"),
    [
        (io.BytesIO(b"foo"), False),
        (io.BytesIO(b""), False),
        (io.BytesIO(b" "), True),
        (io.BytesIO(b"  "), True),
        (io.BytesIO(b"  \n"), True),
        (io.BytesIO(b"    \n"), True),
    ],
)
def test_skipOverWhitespace(stream, expected):
    assert PyPDF2._utils.skip_over_whitespace(stream) == expected


def test_readUntilWhitespace():
    assert PyPDF2._utils.read_until_whitespace(io.BytesIO(b"foo"), maxchars=1) == b"f"


@pytest.mark.parametrize(
    ("stream", "remainder"),
    [
        (io.BytesIO(b"% foobar\n"), b""),
        (io.BytesIO(b""), b""),
        (io.BytesIO(b" "), b" "),
        (io.BytesIO(b"% foo%\nbar"), b"bar"),
    ],
)
def test_skipOverComment(stream, remainder):
    PyPDF2._utils.skip_over_comment(stream)
    assert stream.read() == remainder


def test_readUntilRegex_premature_ending_raise():
    import re

    stream = io.BytesIO(b"")
    with pytest.raises(PdfStreamError) as exc:
        PyPDF2._utils.read_until_regex(stream, re.compile(b"."))
    assert exc.value.args[0] == "Stream has ended unexpectedly"


def test_readUntilRegex_premature_ending_name():
    import re

    stream = io.BytesIO(b"")
    assert (
        PyPDF2._utils.read_until_regex(stream, re.compile(b"."), ignore_eof=True) == b""
    )


@pytest.mark.parametrize(
    ("a", "b", "expected"),
    [
        (((3,),), ((7,),), ((21,),)),
        (((3, 7),), ((5,), (13,)), ((3 * 5.0 + 7 * 13,),)),
        (((3,), (7,)), ((5, 13),), ((3 * 5, 3 * 13), (7 * 5, 7 * 13))),
    ],
)
def test_matrixMultiply(a, b, expected):
    assert PyPDF2._utils.matrix_multiply(a, b) == expected


def test_markLocation():
    stream = io.BytesIO(b"abde" * 6000)
    PyPDF2._utils.mark_location(stream)
    os.remove("PyPDF2_pdfLocation.txt")  # cleanup


def test_hexStr():
    assert PyPDF2._utils.hex_str(10) == "0xa"


def test_b():
    assert PyPDF2._utils.b_("foo") == b"foo"
    assert PyPDF2._utils.b_("😀") == "😀".encode()
    assert PyPDF2._utils.b_("‰") == "‰".encode()
    assert PyPDF2._utils.b_("▷") == "▷".encode()


def test_deprecate_no_replacement():
    with pytest.raises(PendingDeprecationWarning) as exc:
        PyPDF2._utils.deprecate_no_replacement("foo")
    assert exc.value.args[0] == "foo is deprecated and will be removed in PyPDF2 3.0.0."
