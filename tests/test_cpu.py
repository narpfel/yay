from pathlib import Path

from yay.cpu import make_cpu
from yay.helpers import config_filename


# Very crude, but this tests whether `make_cpu` finds the same file regardless
# of how it is called.
def test_make_cpu():
    assert make_cpu(
        Path(config_filename("cpu_configurations/AT89S8253.yml"))
    ).keys() == make_cpu("AT89S8253").keys()
