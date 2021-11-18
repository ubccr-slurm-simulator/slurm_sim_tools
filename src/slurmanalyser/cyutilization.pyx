cimport cython
cimport numpy as np
import pandas as pd
from pandas._libs.tslibs.nattype cimport NPY_NAT
np.import_array()

ctypedef fused intfloat:
    np.int64_t
    double

@cython.boundscheck(False) # turn off bounds-checking for entire function
@cython.wraparound(False)  # turn off negative index wrapping for entire function
def calc_utilization_cy(double[:] util, np.int64_t[:] index, np.int64_t[:] start, np.int64_t[:] end, intfloat[:] resources_count):
    # util and index same lenght
    if util.shape[0]!=index.shape[0]:
        raise IndexError(f"util{util.shape[0]} and index{index.shape[0]} should be same size ")
    # index length >=2
    if util.shape[0] <= 2:
        raise IndexError(f"util and index should be longer than 2 but it is {util.shape[0]}")
    # start, end, resources_count same length
    if start.shape[0]!=end.shape[0] or start.shape[0]!=resources_count.shape[0]:
        raise IndexError(f"start{start.shape[0]}, end{end.shape[0]} and resources_count{resources_count.shape[0]} should be same size ")
    # time resolution should be same in start, end, index, can not check it here

    cdef Py_ssize_t i
    cdef Py_ssize_t j
    cdef Py_ssize_t it0
    cdef Py_ssize_t it1
    cdef Py_ssize_t it2
    cdef Py_ssize_t it3

    cdef Py_ssize_t t0 = index[0]

    cdef np.int64_t util_start_time = index[0]
    cdef np.int64_t freq = index[1] - index[0]
    cdef double rev_freq = 1.0/freq
    cdef np.int64_t util_end_time_incl = index[index.shape[0]-1] + freq

    # chack that freq is same through out
    i = 0
    for j in range(1,index.shape[0]):
        i+= freq != index[j] - index[j-1]
    if i != 0:
        raise IndexError(f"Freq (step between adjustment items) in datetime index should be same,"
                         f" but it is not {i} different from first sterp")

    for i in range(start.shape[0]):
        #start[i]+=1000000000
        #print(start[i],end[i],resources_count[i], NPY_NAT,end[i]==NPY_NAT)
        #for j in range(start[i], end[i]):
        #    util[j]=util[j]+resources_count

        # check that start_time and end_time are within util range
        if start[i]==NPY_NAT and end[i]==NPY_NAT:
            continue
        if start[i]==NPY_NAT:
            raise ValueError(f"start_time({start[i]}) can not be NaT without end_time({end[i]}) been NaT too")
        if end[i]==NPY_NAT:
            end[i] = util_end_time_incl

        if start[i] >util_end_time_incl:
            continue
        if end[i] < util_start_time:
            continue
        if start[i] < util_start_time:
            start[i] = util_start_time
        if end[i] > util_end_time_incl:
            end[i] = util_end_time_incl

        if end[i] < start[i]:
            raise ValueError(f"end_time({end[i]}) < start_time({start[i]} for record {i})")

        #print(start[i],end[i],resources_count[i], NPY_NAT,end[i]==NPY_NAT)
        # general case:
        # | - time pints
        # - - job duration
        # t0  t1  t2  t3
        # |  -|---|---|-  |
        it0 = (start[i]-util_start_time)//freq
        if (start[i]-util_start_time)%freq==0:
            # t,t1  t2  t3
            # |---|---|-  |
            it1 = it0
        else:
            it1 = it0 + 1
        it3 = (end[i]-util_start_time)//freq
        # if t3 == end_time:
        #     # t0  t1  t2,t3
        #     # |  -|---|---|
        #     t2 = t3 - freq
        #     #t3 = t2
        # else:
        #     t2 = t3 - freq
        it2 = it3 - 1
        if it0 != it3:
            #print(it0,it3,freq,start[i],util_start_time + it1*freq,((util_start_time + it1*freq - start[i]) / freq) ,resources_count[i])
            util[it0] += ((util_start_time + it1*freq - start[i]) * rev_freq) * resources_count[i]
            if it3 < util.shape[0]:
                util[it3] += ((end[i] - it3*freq - util_start_time) *rev_freq ) * resources_count[i]
        else:
            # t2   t0,t3  t1
            # |     |  -   |    |
            util[it0] += ((end[i] - start[i]) * rev_freq) * resources_count[i]
        if it2 > it1:
            # greater sign avoid:
            # t2   t0,t3  t1
            # |     |  -   |    |
            # loop to util[t1:t2]
            for j in range(it1, it2+1):
                util[j] += resources_count[i]
        # t0,t1  t2,t3
        # |-------|
        # this case should do too
