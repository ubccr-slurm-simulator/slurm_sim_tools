from typing import Union

import pandas as pd
import numpy as np
from pandas.core.tools.datetimes import DatetimeScalar
from slurmanalyser.cyutilization import calc_utilization_cy

def add_to_util_ref0(util: pd.Series, start_time: DatetimeScalar, end_time: DatetimeScalar,
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


def calc_utilization_ref0(start: pd.Series, end: pd.Series, resource: Union[pd.Series, int, float], freq='1H', t0=None,
                          t1=None):
    if t0 is None:
        t0 = np.min((start.min(), end.min())).floor(freq=freq)
    if t1 is None:
        t1 = np.max((start.max(), end.max())).ceil(freq=freq)

    util_ind = pd.date_range(t0, t1, freq=freq)
    util = pd.Series(0., index=util_ind)

    if isinstance(resource, (int, float)):
        for m_start, m_end in zip(start, end):
            add_to_util_ref0(util, m_start, m_end, resource)
    else:
        for m_start, m_end, m_resource in zip(start, end, resource):
            add_to_util_ref0(util, m_start, m_end, m_resource)
    return util


def calc_utilization(start: pd.DatetimeIndex, end: pd.DatetimeIndex, resources_count, util=None, util_start=None, util_end=None, util_freq='1H'):
    """
    Calculate resource utilization
    @param start: DatetimeIndex with jobs start time
    @param end: DatetimeIndex with dtype=datetime64) with jobs end time
    @param resources_count: resource count to add to util for each job, if scalar each job has same weight
    @param util: (pd.Series with datetime index and dtype=float for main values))if specified will add resource_count inplace
    @param util_start: if set and util is None will use for creation of util Series as start time
    @param util_end: if set and util is None will use for creation of util Series as end time
    @param util_freq: if util is None will use for creation of util Series as freq
    @return: util
    """
    # check datatype
    if not isinstance(start, (pd.DatetimeIndex, pd.Series)):
        raise TypeError(f"start should be pd.DatetimeIndex but it is {type(start)}")

    if not isinstance(end, (pd.DatetimeIndex, pd.Series)):
        raise TypeError(f"end should be pd.DatetimeIndex but it is {type(end)}")

    if isinstance(resources_count, pd.Series):
        m_resources_count = resources_count.values
    elif isinstance(resources_count, np.ndarray):
        m_resources_count = resources_count
    elif isinstance(resources_count,(int,float)):
        m_resources_count = np.full(start.shape[0], resources_count, dtype="double")
    else:
        raise TypeError(f"resource_count should be either pd.Series, np.array or scalar int/float but it is {type(resources_count)}")

    if str(m_resources_count.dtype) not in ('float64', 'int64', 'Int64'):
        raise TypeError(f"resource_count dtype should be either int64/double but it is {m_resources_count.dtype}")

    # check that time resolution is same
    if not str(start.dtype).startswith("datetime64["):
        raise TypeError(f"start dtype should be datetime64[?] but it is {start.dtype}")
    datetime_type = str(start.dtype)
    if str(end.dtype) != datetime_type:
        raise TypeError(f"all datetime-s should have same resolution but start is {start.dtype} and end is {end.dtype}")


    # create our own  util if needed
    if util is None:
        if util_start is None:
            util_start = min(start.min(), end.min()).floor(freq=util_freq)
        elif isinstance(util_start,str):
            util_start = pd.to_datetime(util_start)

        if util_end is None:
            util_end = max(start.max(), end.max()).ceil(freq=util_freq)
        elif isinstance(util_end,str):
            util_end = pd.to_datetime(util_end)

        util_ind = pd.date_range(util_start, util_end, freq=util_freq)
        util = pd.Series(0., index=util_ind)
    #
    if str(util.index.dtype) != datetime_type:
        raise TypeError(f"all datetime-s should have same resolution but start is {start.dtype} and util.index is {util.index.dtype}")

    if str(m_resources_count.dtype) in ('float64',):
        calc_utilization_cy(util.values,util.index.values.view(np.int64), start.values.astype(np.int64),
                            end.values.astype(np.int64), m_resources_count.astype(np.float64))
    else:
        calc_utilization_cy(util.values, util.index.values.view(np.int64), start.values.astype(np.int64),
                            end.values.astype(np.int64), m_resources_count.astype(np.int64))
    return util


def calc_utilization_df(df, freq='1H'):
    """
    Calculate resource utilization
    @param df:
    @param freq:
    @return:
    """
    t0 = np.min((df.Start.min(), df.End.min())).floor(freq=freq)
    t1 = np.max((df.Start.max(), df.End.max())).ceil(freq=freq)
    util_ind = pd.date_range(t0, t1, freq=freq)
    util = pd.Series(0., index=util_ind)
    calc_utilization(df.Start, df.End, 1.0, util)