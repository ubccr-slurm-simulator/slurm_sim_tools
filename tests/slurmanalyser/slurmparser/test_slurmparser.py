import pytest

@pytest.mark.parametrize(
    "line, nfield, split, expected",
    [
        ("field1|field2|field3|field4|field5", 5, "|",
         ['field1', 'field2', 'field3', 'field4', 'field5']),
        ("|field1|field2|field3|field4|field5|", 5, "|",
         ['field1', 'field2', 'field3', 'field4', 'field5']),
        ("|field1|field2|field3|field4|field5|\n", 5, "|",
         ['field1', 'field2', 'field3', 'field4', 'field5']),
        ("field1|field2|field3|field4|fie||ld5", 5, "|",
         ['field1', 'field2', 'field3', 'field4', 'fie||ld5']),
        ("|field1|field2|field3|field4|fie||ld5|\n", 5, "|",
         ['field1', 'field2', 'field3', 'field4', 'fie||ld5']),
    ]
)
def test_split_nfields_1( line, nfield, split, expected):
    from slurmanalyser.slurmparser import SlurmFileParser
    assert SlurmFileParser.split_nfields(line, nfields=nfield, split=split) == expected

def test_slurm_datetime():
    from slurmanalyser.slurmparser import slurm_datetime
    from datetime import datetime

    assert slurm_datetime('2021-08-09T00:06:15') == datetime(2021, 8, 9, 0, 6, 15)


def test_slurm_duration():
    from slurmanalyser.slurmparser import slurm_duration
    from datetime import timedelta

    assert slurm_duration('1-00:06:00') == timedelta(days=1, hours=0, minutes=6,seconds=0)
    assert slurm_duration('1-13:06:00') == timedelta(days=1, hours=13, minutes=6, seconds=0)
    assert slurm_duration('1-07:06:00') == timedelta(days=1, hours=7, minutes=6, seconds=0)
    assert slurm_duration('1-02:06:11') == timedelta(days=1, hours=2, minutes=6, seconds=11)
    assert slurm_duration('00:06:00') == timedelta(hours=0, minutes=6, seconds=0)
    assert slurm_duration('13:06:00') == timedelta(hours=13, minutes=6, seconds=0)
    assert slurm_duration('07:06:00') == timedelta(hours=7, minutes=6, seconds=0)
    assert slurm_duration('02:06:11') == timedelta(hours=2, minutes=6, seconds=11)

def test_slurm_memory():
    '30000M'
    pass