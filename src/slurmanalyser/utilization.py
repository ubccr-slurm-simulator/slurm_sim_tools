from typing import Union

import pandas as pd
from pandas.core.tools.datetimes import DatetimeScalar


def add_to_util(util: pd.Series, start_time: DatetimeScalar, end_time: DatetimeScalar,
                resources_count: Union[int, float] = 1.0):
    """
    add resources_count to utilization from start_time to end_time

    if start_time is NaT raise error, if end_time is NaT assume it runs beyond the end of util
    if start_time and end_time are NaT assumes job didn't run

    @param util: pandas.Series with DatetimeIndex vi set pandas.freq, changed inplace, also returned for convenience
    @param start_time:
    @param end_time:
    @param resources_count: resource count, like cores, nodes, memory
    @return: util
    """
    freq = util.index[1] - util.index[0]
    util_start_time = util.index[0]
    util_end_time_incl = util.index[-1] + freq
    # check that start_time and end_time are within util range
    if end_time < start_time:
        raise ValueError(f"end_time({end_time}) < start_time({start_time})")
    if start_time > util.index[-1]:
        return util
    if end_time < util_start_time:
        return util
    if start_time < util_start_time:
        start_time = util_start_time
    if end_time > util_end_time_incl:
        end_time = util_end_time_incl
    if pd.isna(start_time) and pd.isna(end_time):
        return util
    if pd.isna(start_time):
        raise ValueError(f"start_time({start_time}) can not be NaT without end_time({end_time}) been NaT too")
    if pd.isna(end_time):
        end_time = util_end_time_incl
    # general case:
    # | - time pints
    # - - job duration
    # t0  t1  t2  t3
    # |  -|---|---|-  |
    t0 = start_time.floor(freq=freq)
    if t0 == start_time:
        # t,t1  t2  t3
        # |---|---|-  |
        t1 = t0
    else:
        t1 = t0 + freq
    t3 = end_time.floor(freq=freq)
    # if t3 == end_time:
    #     # t0  t1  t2,t3
    #     # |  -|---|---|
    #     t2 = t3 - freq
    #     #t3 = t2
    # else:
    #     t2 = t3 - freq
    t2 = t3 - freq

    if t0 != t3:
        util[t0] += ((t1 - start_time) / freq) * resources_count
        if t3 < util_end_time_incl:
            util[t3] += ((end_time - t3) / freq) * resources_count
    else:
        # t2   t0,t3  t1
        # |     |  -   |    |
        util[t0] += ((end_time - start_time) / freq) * resources_count
    if t2 > t1:
        # greater sign avoid:
        # t2   t0,t3  t1
        # |     |  -   |    |
        util[t1:t2] += resources_count
    # t0,t1  t2,t3
    # |-------|
    # this case should do too
    return util


def calc_utilization(df, freq='1H'):
    t0 = df.loc[:,('submit', 'eligible', 'start', 'end')].min().min().floor(freq=freq)
    t1 = df.loc[:,('submit', 'eligible', 'start', 'end')].max().max().ceil(freq=freq)
    util_ind = pd.date_range(t0, t1, freq=freq)
    util = pd.Series(0., index=util_ind)
    for start,end in df.loc[:, 'start':'end'].itertuples(index=False,name=None):
        add_to_util(util, start, end, 1)
    return util


class Utilization:
    def __init__(self):
        pass
