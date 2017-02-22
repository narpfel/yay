from glob import glob
from os import path

from pytest import mark
from ihex import IHex

from yay.cli import main


def read(hex_filename):
    return IHex.read_file(hex_filename).areas[0]


@mark.parametrize(
    "yay_filename", glob("examples/**/*.yay")
)
def test_example(tmpdir, yay_filename):
    expected_filename = path.splitext(yay_filename)[0] + ".hex"
    test_file = tmpdir.join("output.hex")
    main([yay_filename, "-o", test_file.strpath])
    assert read(test_file.strpath) == read(expected_filename)
