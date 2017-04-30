from itertools import chain
from pathlib import Path
import shutil

from pytest import mark
from ihex import IHex

from yay.cli import main


def read(hex_filename):
    return IHex.read_file(hex_filename).areas[0]


@mark.parametrize(
    "yay_filename", chain(
        Path("examples/").glob("**/*.yay"),
        Path("tests/test_yay_files").glob("**/*.yay"),
    )
)
def test_example(tmpdir, yay_filename):
    expected_filename = yay_filename.with_suffix(".hex")
    # Copy to tempdir to prevent bytecode caching
    yay_filename = shutil.copy(yay_filename, tmpdir)
    test_file = tmpdir.join("output.hex")

    main([yay_filename, "-o", test_file.strpath])

    if not expected_filename.exists():
        expected_filename = tmpdir.join("expected.hex")
        main([
            yay_filename,
            "-o", expected_filename.strpath,
            "--main_class", "Expected",
        ])

    assert read(test_file) == read(expected_filename)
