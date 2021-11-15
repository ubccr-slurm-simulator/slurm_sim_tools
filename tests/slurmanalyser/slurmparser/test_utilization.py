import numpy as np
import pandas as pd
import pytest

from slurmanalyser.utilization import add_to_util_single_wrap


def add_to_util_single_wrap_single_wrap(util, start, end, resoource_count):

    add_to_util_single_wrap(util, pd.to_datetime([start]), pd.to_datetime([end]), np.array([resoource_count], dtype="double"))
    return util
    
def test_utilization():
    import numpy as np
    import pandas as pd

    
    util_ind = pd.date_range("2021-06-01 14:00:00", "2021-06-01 19:00:00", freq="30Min")

    util = add_to_util_single_wrap(pd.Series(0., index=util_ind), "2021-06-01T15:25:37", "2021-06-01T17:31:21", 1.0)
    assert np.all(np.isclose(util.values, [0., 0., 0.14611111, 1., 1., 1., 1., 0.045, 0., 0., 0.]))
    util = add_to_util_single_wrap(pd.Series(0., index=util_ind), "2021-06-01T15:25:37", "2021-06-01T15:29:21", 1.0)
    assert np.all(np.isclose(util.values, [0., 0., 0.12444444, 0., 0., 0., 0., 0., 0., 0., 0.]))
    util = add_to_util_single_wrap(pd.Series(0., index=util_ind), "2021-06-01T15:25:37", "2021-06-01T15:39:21", 1.0)
    assert np.all(np.isclose(util.values, [0., 0., 0.14611111, 0.31166667, 0., 0., 0., 0., 0., 0., 0.]))
    util = add_to_util_single_wrap(pd.Series(0., index=util_ind), "2021-06-01T13:25:37", "2021-06-02T15:39:21", 1.0)
    assert np.all(np.isclose(util.values, [1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1.]))
    util = add_to_util_single_wrap(pd.Series(0., index=util_ind), "2021-06-01T14:15:00", "2021-06-01T21:15:00", 1.0)
    assert np.all(np.isclose(util.values, [0.5, 1., 1., 1., 1., 1., 1., 1., 1., 1., 1.]))
    util = add_to_util_single_wrap(pd.Series(0., index=util_ind), "2021-06-01T13:25:37", "2021-06-01T19:15:00", 1.0)
    assert np.all(np.isclose(util.values, [1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 0.5]))
    util = add_to_util_single_wrap(pd.Series(0., index=util_ind), "2021-06-01T14:15:00", "2021-06-01T19:15:00", 10.0)
    assert np.all(np.isclose(util.values, [5., 10., 10., 10., 10., 10., 10., 10., 10., 10., 5.]))
    util = add_to_util_single_wrap(pd.Series(0., index=util_ind), "2021-06-01T16:00:00", "2021-06-01T17:10:00", 2.0)
    assert np.all(np.isclose(util.values, [0., 0., 0., 0., 2., 2., 2.*1/3, 0., 0., 0., 0.]))
    util = add_to_util_single_wrap(pd.Series(0., index=util_ind), "2021-06-01T16:10:00", "2021-06-01T17:30:00", 2.0)
    assert np.all(np.isclose(util.values, [0., 0., 0., 0., 2.*2/3, 2., 2., 0., 0., 0., 0.]))
    util = add_to_util_single_wrap(pd.Series(0., index=util_ind), "2021-06-01T16:30:00", "2021-06-01T17:30:00", 2.0)
    assert np.all(np.isclose(util.values, [0., 0., 0., 0., 0., 2., 2., 0., 0., 0., 0.]))
    util = add_to_util_single_wrap(pd.Series(0., index=util_ind), "2021-06-01T16:50:00", "2021-06-01T17:20:00", 2.0)
    assert np.all(np.isclose(util.values, [0., 0., 0., 0., 0., 2/3, 4/3, 0., 0., 0., 0.]))
    util = add_to_util_single_wrap(pd.Series(0., index=util_ind), "2021-06-01T17:10:00", "2021-06-01T17:20:00", 2.0)
    assert np.all(np.isclose(util.values, [0., 0., 0., 0., 0., 0., 2/3, 0., 0., 0., 0.]))
    util = add_to_util_single_wrap(pd.Series(0., index=util_ind), "2021-06-01T17:00:00", "2021-06-01T17:20:00", 2.0)
    assert np.all(np.isclose(util.values, [0., 0., 0., 0., 0., 0., 4/3, 0., 0., 0., 0.]))
    util = add_to_util_single_wrap(pd.Series(0., index=util_ind), "2021-06-01T17:20:00", "2021-06-01T17:30:00", 2.0)
    assert np.all(np.isclose(util.values, [0., 0., 0., 0., 0., 0., 2/3, 0., 0., 0., 0.]))

    with pytest.raises(ValueError):
        util = add_to_util_single_wrap(pd.Series(0., index=util_ind), "2021-06-01T17:40:00", "2021-06-01T17:30:00", 2.0)
