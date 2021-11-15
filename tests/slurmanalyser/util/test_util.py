import pytest


def test_util_norm_si():
    """
    checking util_norm_si
    @return:
    """
    from slurmanalyser.utils import util_norm_si
    import pandas as pd
    import numpy as np

    v = pd.Series(['1','1K','1M','1 K', '1 k','1.3 M', '1.5m', '','Unknown','NA','NaN'])
    ref = pd.Series([1, 1000, 1000000, 1000, 1000, 1300000, 1500000, pd.NA, pd.NA, pd.NA, pd.NA], dtype="Int64")

    assert ref.equals(util_norm_si(v, convert_to_int=True, check_na=True))

    v = pd.Series(['1', '1K', '1M', '1 K', '1 k', '1.3 M', '1.5m', '', 'Unknown', 'NA', 'NaN', 'NAT', "something"])
    ref = pd.Series([1, 1000, 1000000, 1000, 1000, 1300000, 1500000, pd.NA, pd.NA, pd.NA, pd.NA, pd.NA, pd.NA], dtype="Int64")
    assert ref.equals(util_norm_si(v, convert_to_int=True))
    assert ref.equals(util_norm_si(v, convert_to_int=True, check_na="warning"))
    with pytest.raises(ValueError):
        x = util_norm_si(v, convert_to_int=True, check_na="error")

    v = pd.Series(
        ['1', '1024', '1000', '1k', '1 K', '1 k', '1.3 M', '1.5m', '3.6 G', '7.9g', '2134.55T', '', 'Unknown', 'NA', 'NaN'])
    ref = pd.Series(
        [1, 1024, 1000, 1000, 1000, 1000, 1300000, 1500000, 3600000000, 7900000000, 2134550000000000, pd.NA, pd.NA, pd.NA, pd.NA],
        dtype="Int64")
    assert ref.equals(util_norm_si(v, convert_to_int=True, check_na="warning"))

    v = pd.Series(
        ['1', '1024', '1000', '1k', '1 K', '1 k', '1.3 M', '1.5m', '3.6 G', '7.9g', '2134.55T', '', 'Unknown', 'NA', 'NaN'])
    ref = pd.Series(
        [0, 1, 1, 1, 1, 1, 1300, 1500, 3600000, 7900000, 2134550000000, pd.NA, pd.NA, pd.NA, pd.NA],
        dtype="Int64")
    assert ref.equals(util_norm_si(v, return_in='k', convert_to_int=True, check_na="warning"))

    v = pd.Series(
        ['1', '1024', '1000', '1k', '1 K', '1 k', '1.3 M', '1.5m', '3.6 G', '7.9g', '2134.55T', '', 'Unknown', 'NA',
         'NaN'])
    ref = pd.Series(
        [1, 1024, 1000, 1024, 1024, 1024, 1363149, 1572864, 3865470566, 8482560410, 2346962545069261, pd.NA, pd.NA,
         pd.NA, pd.NA],
        dtype="Int64")
    assert ref.equals(util_norm_si(v, convert_to_int=True, check_na="warning",use1024=True))

    v = pd.Series(
        ['1', '1024', '1000', '1k', '1 K', '1 k', '1.3 M', '1.5m', '3.6 G', '7.9g', '2134.55T', '', 'Unknown', 'NA',
         'NaN'])
    ref = pd.Series(
        [1.00000e-03, 1.02400e+00, 1.00000e+00, 1.00000e+00, 1.00000e+00, 1.00000e+00, 1.30000e+03, 1.50000e+03,
         3.60000e+06, 7.90000e+06, 2.13455e+12, np.nan, np.nan, np.nan, np.nan],
        dtype="float64")
    assert np.all(np.isclose(ref, util_norm_si(v, return_in='k'), equal_nan=True))

def test_util_to_int():
    from slurmanalyser.utils import util_to_int
    import pandas as pd
    import numpy as np

    from slurmanalyser.utils import util_to_int
    v = pd.Series(['1', '1024', '1000', '1234544', '1.234e12', '', 'Unknown', 'NA', 'NaN'])
    ref = pd.Series([1, 1024, 1000, 1234544, 1234000000000, pd.NA, pd.NA, pd.NA, pd.NA], dtype="Int64")
    assert ref.equals(util_to_int(v))

    v = pd.Series(['1', '6.234', '6.78', '1024', '1000', '1234544', '1.234e12', '', 'Unknown', 'NA', 'NaN'])
    ref = pd.Series([1, 6, 7, 1024, 1000, 1234544, 1234000000000, pd.NA, pd.NA, pd.NA, pd.NA], dtype="Int64")
    with pytest.raises(Exception):
        util_to_int(v)
    assert ref.equals(util_to_int(v, round=True))


def test_util_to_float():
    import pandas as pd
    import numpy as np

    from slurmanalyser.utils import util_to_float


    v = pd.Series(['1', '6.234', '6.78', '10.24', '1000', '1234544', '1.234e-12', '', 'Unknown', 'NA', 'NaN'])
    ref = pd.Series([1, 6.234, 6.78, 10.24, 1000., 1234544., 1.234e-12, np.nan, np.nan, np.nan, np.nan], dtype="float64")
    #with pytest.raises(Exception):
    #    util_to_int(v)
    assert np.all(np.isclose(ref, util_to_float(v, check_na='error'), equal_nan=True))

    v = pd.Series(['1', '6.234', '6.78', '10.24', '1000', '1234544', '1.234e-12', '', 'Unknown', 'NA', 'NaN','sadsad'])
    ref = pd.Series([1, 6.234, 6.78, 10.24, 1000., 1234544., 1.234e-12, np.nan, np.nan, np.nan, np.nan],
                    dtype="float64")
    with pytest.raises(Exception):
        util_to_float(v, check_na='error')


def test_util_slurm_datetime_to_datetime():
    from slurmanalyser.utils import util_slurm_datetime_to_datetime
    import pandas as pd

    v = pd.Series(['2011-11-04T00:05:23', '2019-03-07T14:05:23', '', 'Unknown', 'NA', 'NaN', 'NaT','nan'])
    ref = pd.to_datetime(pd.Series(['2011-11-04 00:05:23', '2019-03-07 14:05:23', 'NaT', 'NaT', 'NaT', 'NaT', 'NaT', 'NaT']), errors='coerce').astype('datetime64[ns]')
    assert ref.equals(util_slurm_datetime_to_datetime(v, check_na='error'))

    v = pd.Series(['2011-11-04T00:05:23', '2019-03-07T14:05:23', '', 'Unknown', 'NA', 'NaN', 'NaT', 'nan', 'oneday'])
    with pytest.raises(Exception):
        util_slurm_datetime_to_datetime(v, check_na='error')

def test_util_slurm_duration_to_duration():
    from slurmanalyser.utils import util_slurm_duration_to_duration
    import pandas as pd

    v = pd.Series(["123", "132:45","12:05:55", "11-12", "11-12:05", "11-12:05:55", '', 'Unknown', 'NA', 'NaN', 'NaT','nan'])
    ref=pd.Series([7380000000000, 7965000000000, 43555000000000, 993600000000000, 993900000000000, 993955000000000, 'NaT', 'NaT', 'NaT', 'NaT', 'NaT', 'NaT'], dtype='timedelta64[ns]')
    assert ref.equals(util_slurm_duration_to_duration(v, check_na='error'))

    v = pd.Series(["123", "132:45","12:05:55", "11-12", "11-12:05", "11-12:05:55", '', 'Unknown', 'NA', 'NaN', 'NaT','nan', 'oneday'])
    with pytest.raises(Exception):
        util_slurm_duration_to_duration(v, check_na='error')

