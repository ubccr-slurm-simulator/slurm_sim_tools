import datetime
from slurmanalyser.slurmparser import slurm_datetime, SlurmDuration, SlurmMemory
from slurmanalyser.slurmparser import SlurmFileParser
import logging as log
import multiprocessing as mp
import sys
import tqdm
import numpy as np
import pandas as pd
import re

from slurmanalyser.utils import get_file_open

import array

re_duration_str = r"(?:\d+:\d{2}:\d{2}|\d+-\d+:\d{2}:\d{2}|\d{1,2}:\d{2})"
re_datetime_str = r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}"
re_dur_unk_str = r"(?:\d+:\d{2}:\d{2}|\d+-\d+:\d{2}:\d{2}|\d{1,2}:\d{2}|Unknown)"
re_dur_empty_unk_str = r"(?:\d+:\d{2}:\d{2}|\d+-\d+:\d{2}:\d{2}|\d{1,2}:\d{2}|Unknown|)"
re_datetime_unk_str = r"(?:\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}|Unknown)"
re_datetime_empty_unk_str = r"(?:\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}|Unknown|)"
re_exitcode_str = r"\d+:\d+"
re_exitcode_empty_str = r"(?:\d+:\d+|)"
re_digits_empty_str = r"(?:[0-9]+|)"
re_digits_str = r"[0-9]+"
re_any_nospec_str = r"[^|\n]*"
re_any_str = r".*"

re_duration = re.compile(re_duration_str)
re_datetime = re.compile(re_datetime_str)
re_dur_unk = re.compile(re_dur_unk_str)
re_dur_empty_unk = re.compile(re_dur_empty_unk_str)
re_datetime_unk = re.compile(re_datetime_unk_str)
re_datetime_empty_unk = re.compile(re_datetime_empty_unk_str)
re_exitcode = re.compile(re_exitcode_str)
re_exitcode_empty = re.compile(re_exitcode_empty_str)
re_digits_empty = re.compile(re_digits_empty_str)

cols_pattern = {
    'Container': re_any_nospec_str,
    "ConsumedEnergy": re_digits_empty_str,
    "ConsumedEnergyRaw": re_digits_empty_str,
    "CPUTime": re_duration_str,
    "CPUTimeRAW": re_digits_str,
    "DBIndex": re_digits_str,
    "DerivedExitCode": re_exitcode_empty_str,
    "Elapsed": re_duration_str,
    "ElapsedRaw": re_digits_str,
    "Eligible": re_datetime_unk_str,
    "End": re_datetime_unk_str,
    "ExitCode": re_exitcode_empty_str,
    "Flags": re_any_nospec_str,
    "GID": re_digits_empty_str,
    "JobID": re_any_nospec_str,
    "JobIDRaw": re_any_nospec_str,
    "JobName": re_any_str,
    "Layout": re_any_nospec_str,
}
ConsumedEnergy_ExitCode = re.compile("\|".join((cols_pattern[c] for c in ('ConsumedEnergy', 'ConsumedEnergyRaw', 'CPUTime', 'CPUTimeRAW', 'DBIndex', 'DerivedExitCode',
'Elapsed', 'ElapsedRaw', 'Eligible', 'End', 'ExitCode'))))

columns_dump1 = ['Account', 'AdminComment', 'AllocCPUS', 'AllocNodes', 'AllocTRES', 'AssocID', 'AveCPU', 'AveCPUFreq',
'AveDiskRead', 'AveDiskWrite', 'AvePages', 'AveRSS', 'AveVMSize', 'BlockID', 'Cluster', 'Comment', 'Constraints',
'Container', 'ConsumedEnergy', 'ConsumedEnergyRaw', 'CPUTime', 'CPUTimeRAW', 'DBIndex', 'DerivedExitCode',
'Elapsed', 'ElapsedRaw', 'Eligible', 'End', 'ExitCode', 'Flags', 'GID', 'Group', 'JobID', 'JobIDRaw', 'JobName',
'Layout', 'MaxDiskRead', 'MaxDiskReadNode', 'MaxDiskReadTask', 'MaxDiskWrite', 'MaxDiskWriteNode',
'MaxDiskWriteTask', 'MaxPages', 'MaxPagesNode', 'MaxPagesTask', 'MaxRSS', 'MaxRSSNode', 'MaxRSSTask',
'MaxVMSize', 'MaxVMSizeNode', 'MaxVMSizeTask', 'McsLabel', 'MinCPU', 'MinCPUNode', 'MinCPUTask', 'NCPUS',
'NNodes', 'NodeList', 'NTasks', 'Priority', 'Partition', 'QOS', 'QOSRAW', 'Reason', 'ReqCPUFreq', 'ReqCPUFreqMin',
'ReqCPUFreqMax', 'ReqCPUFreqGov', 'ReqCPUS', 'ReqMem', 'ReqNodes', 'ReqTRES', 'Reservation',
'ReservationId', 'Reserved', 'ResvCPU', 'ResvCPURAW', 'Start', 'State', 'Submit', 'SubmitLine', 'Suspended',
'SystemCPU', 'SystemComment', 'Timelimit', 'TimelimitRaw', 'TotalCPU', 'TRESUsageInAve', 'TRESUsageInMax',
'TRESUsageInMaxNode', 'TRESUsageInMaxTask', 'TRESUsageInMin', 'TRESUsageInMinNode', 'TRESUsageInMinTask',
'TRESUsageInTot', 'TRESUsageOutAve', 'TRESUsageOutMax', 'TRESUsageOutMaxNode', 'TRESUsageOutMaxTask',
'TRESUsageOutMin', 'TRESUsageOutMinNode', 'TRESUsageOutMinTask', 'TRESUsageOutTot', 'UID', 'User',
'UserCPU', 'WCKey', 'WCKeyID', 'WorkDir']


def get_colnames_from_sacclog(filename):
    m_open = get_file_open(filename)
    with m_open(filename, 'rt') as fin:
        line = next(fin).rstrip()
        colnames = line.split("|")
    return colnames


def parse_sacclog_iter(filename, colnames=None):
    """
    return list of lists parsed from sacct logs, take care of | in JobNames as well as
    | in both Constraints and JobNames in certain dumps
    @param filename:
    @param colnames:
    @return:
    """
    # cdef int ncols
    # cdef int iline
    # cdef int i
    # cdef int ipos
    # cdef int icol_jobname
    # cdef int icol_constraints
    # cdef int iConsumedEnergy
    # cdef int iConsumedEnergyRaw
    # cdef int iCPUTime
    # cdef int iCPUTimeRAW
    # cdef int iElapsed
    # cdef int iElapsedRaw
    # cdef int iEligible
    # cdef int iEnd
    # cdef int iExitCode
    # cdef int count
    # cdef int extra_pipe
    # cdef int matches
    # cdef int i_start
    # cdef int ipos_start
    # cdef int pipe_removed
    # cdef array.array col_pos

    m_open = get_file_open(filename)

    with m_open(filename, 'rt') as fin:
        if colnames is None:
            line = next(fin).rstrip()
            colnames = line.split("|")

        iline = 1
        ncols = len(colnames)
        col_pos = array.array('l', [0] * (ncols + 1))
        if colnames == columns_dump1:
            # dump schema 1. columns Constraint and JobName can contain |
            print("dump schema 1")
            icol_jobname = colnames.index("JobName")
            icol_constraints = colnames.index("Constraints")
            # ConsumedEnergy=|0|
            iConsumedEnergy = colnames.index("ConsumedEnergy")
            # ConsumedEnergyRaw=|0|
            iConsumedEnergyRaw = colnames.index("ConsumedEnergyRaw")
            # CPUTime=|06:12:45|
            iCPUTime = colnames.index("CPUTime")
            # CPUTimeRAW=|22365|
            iCPUTimeRAW = colnames.index("CPUTimeRAW")
            # DBIndex=|13263062|
            # Elapsed=|06:12:45|
            iElapsed = colnames.index("Elapsed")
            # ElapsedRaw=|22365|
            iElapsedRaw = colnames.index("ElapsedRaw")
            # Eligible=|2021-09-30T21:52:50|
            iEligible = colnames.index("Eligible")
            # End=|2021-10-01T04:05:35|
            iEnd = colnames.index("End")
            # ExitCode=|0:0|
            iExitCode = colnames.index("ExitCode")

            count = 0
            for line in fin:
                # no | in comment or jobname
                extra_pipe = line.count("|") - (ncols-1)
                iline += 1
                if extra_pipe == 0:
                    yield line.rstrip().split("|")
                    continue
                # positions to colmment
                i = 0
                ipos = -1
                col_pos[i] = ipos
                while i < icol_constraints:
                    i += 1
                    ipos = line.find("|", ipos + 1)
                    col_pos[i] = ipos
                #'Comment', 'Constraints', 'Container', 'ConsumedEnergy', 'ConsumedEnergyRaw', 'CPUTime'
                i_start = i
                ipos_start = ipos
                pipe_removed = 0
                while True:
                    while i <= icol_jobname:
                        i += 1
                        ipos = line.find("|", ipos + 1)
                        col_pos[i] = ipos
                    # the above need to be redone untill some types of field matches
                    matches = 0
                    # Comment=||
                    # Constraints=||
                    # Container=||
                    # ConsumedEnergy=|0|
                    s = line[col_pos[iConsumedEnergy] + 1:col_pos[iConsumedEnergy + 1]]
                    matches += s == "" or s.isdigit()
                    # ConsumedEnergyRaw=|0|
                    s = line[col_pos[iConsumedEnergyRaw] + 1:col_pos[iConsumedEnergyRaw + 1]]
                    matches += s == "" or s.isdigit()
                    # CPUTime=|06:12:45|
                    # s = line[col_pos[iCPUTime] + 1:col_pos[iCPUTime + 1]]
                    matches += bool(re_dur_empty_unk.fullmatch(line, col_pos [iCPUTime] + 1, col_pos[iCPUTime + 1]))
                    # CPUTimeRAW=|22365|
                    s = line[col_pos[iCPUTimeRAW] + 1:col_pos[iCPUTimeRAW + 1]]
                    matches += s.isdigit()
                    # DBIndex=|13263062|
                    # DerivedExitCode=||
                    # Elapsed=|06:12:45|
                    # s = line[col_pos[iElapsed] + 1:col_pos[iElapsed + 1]]
                    matches += bool(re_dur_empty_unk.fullmatch(line, col_pos[iElapsed] + 1, col_pos[iElapsed + 1]))
                    # ElapsedRaw=|22365|
                    s = line[col_pos[iElapsedRaw] + 1:col_pos[iElapsedRaw + 1]]
                    matches += s.isdigit()
                    # Eligible=|2021-09-30T21:52:50|
                    # s = line[col_pos[iEligible] + 1:col_pos[iEligible + 1]]
                    matches += bool(re_datetime_unk.fullmatch(line, col_pos[iEligible] + 1, col_pos[iEligible + 1]))
                    # End=|2021-10-01T04:05:35|
                    #s = line[]
                    matches += bool(re_datetime_unk.fullmatch(line, col_pos[iEnd] + 1, col_pos[iEnd + 1]))
                    # ExitCode=|0:0|
                    # Flags=||
                    # GID=||
                    # Group=||
                    # JobID=|7924238.extern|
                    # JobIDRaw=|7924238.extern|
                    # JobName=|extern|
                    # print(matches)
                    # m2 = bool(ConsumedEnergy_ExitCode.fullmatch(line, col_pos[iConsumedEnergy] + 1, col_pos[iExitCode + 1]))
                    #
                    # if m2 != (matches >= 8):
                    #     print("ERROR")


                    pipe_removed += 1
                    if matches >= 8:
                        break
                    elif pipe_removed > extra_pipe:
                        fields = [line[col_pos[i] + 1:col_pos[i + 1]] for i in range(ncols)]
                        print("can not read, too many |")

                        print(iline, line.count("|") + 1, ncols, matches)
                        print(line)
                        for k, v in zip(colnames, fields):
                            print(f"{k}=|{v}|")
                        raise ValueError("can not read, too many |")
                    else:
                        i = i_start
                        ipos = line.find("|", ipos_start + 1)
                        ipos_start = ipos


                #
                i = ncols
                ipos = len(line) - 1
                col_pos[i] = ipos
                while i > icol_jobname + 1:
                    i -= 1
                    ipos = line.rfind("|", 0, ipos)
                    col_pos[i] = ipos

                fields = [line[col_pos[i] + 1:col_pos[i + 1]] for i in range(ncols)]
                yield fields
        else:
            # assume only  JobName can contain |
            icol_jobname = colnames.index("JobName")


            count = 0
            for line in fin:
                i = 0
                ipos = -1
                col_pos[i] = ipos
                while i <= icol_jobname:
                    i += 1
                    ipos = line.find("|", ipos+1)
                    col_pos[i] = ipos
                i = ncols
                ipos = len(line)-1
                col_pos[i] = ipos
                while i > icol_jobname+1:
                    i -= 1
                    ipos = line.rfind("|", 0, ipos)
                    col_pos[i] = ipos

                fields = [line[col_pos[i]+1:col_pos[i+1]] for i in range(ncols)]
                yield fields

def get_init_sacctlog_df(filename, colnames=None):
    import pandas
    if colnames is None:
        colnames = get_colnames_from_sacclog(filename)
    df = pandas.DataFrame(
        parse_sacclog_iter(filename),
        columns=colnames)
    return df




TRES_SPECS_FIELDS = {
    'billing': {'convert': int},
    'cpu': {'convert': int},
    'mem': {'convert': SlurmMemory.from_string},
    'node': {'convert': int},

}

class TResSpecs:
    def __init__(self, **kwargs):
        for k,v in kwargs.items():
            if k in TRES_SPECS_FIELDS:
                self.__setattr__(k, TRES_SPECS_FIELDS[k]['convert'](v))

    def __str__(self):
        attrs = []
        for k in [a for a in dir(self) if not a.startswith('__') and not callable(getattr(self, a))]:
            attrs.append(f'{k}={str(self.__getattribute__(k))}')
        return ",".join(attrs)

    def __eq__(self, other):
        for k in TRES_SPECS_FIELDS.keys():
            left = getattr(self, k, None)
            right = getattr(other, k, None)
            if getattr(self, k, None) != getattr(other, k, None):
                return False
        return True

    @staticmethod
    def from_string(line):
        "billing=12,cpu=12,mem=187000M,node=1"
        if line.strip() == '':
            return TResSpecs()
        return TResSpecs(**dict((v.split("=", maxsplit=1) for v in line.split(","))))


# sacct log fields their internal name, converter to internal format and salloc log name
# as specified for sacct utility
SACCTLOG_JOB_FIELDS = {
    'jobid_str': {'convert': str, 'sacctlog_name': 'jobid'},
    'jobid_raw_str': {'convert': str, 'sacctlog_name': 'jobidraw'},
    'cluster': {'convert': str},
    'partition': {'convert': str},
    'account': {'convert': str},
    'group': {'convert': str},
    'gid': {'convert': int},
    'user': {'convert': str},
    'uid': {'convert': int},
    'submit': {'convert': slurm_datetime},
    'eligible': {'convert': slurm_datetime},
    'start': {'convert': slurm_datetime},
    'end': {'convert': slurm_datetime},
    'elapsed': {'convert': SlurmDuration.from_string},
    'exitcode': {'convert': str},
    'state': {'convert': str},
    'nnodes': {'convert': int},
    'ncpus': {'convert': int},
    'req_cpus': {'convert': int, 'sacctlog_name': 'reqcpus'},
    'req_mem': {'convert': SlurmMemory.from_string, 'sacctlog_name': 'reqmem'},
    'req_tres': {'convert': TResSpecs.from_string, 'sacctlog_name': 'reqtres'},
    'alloc_tres': {'convert': TResSpecs.from_string, 'sacctlog_name': 'alloctres'},
    'timelimit': {'convert': SlurmDuration.from_string},
    'nodelist': {'convert': str},
    'jobname': {'convert': str}
}
SACCTLOG_NAME_TO_SLURM_INT = {v.get('sacctlog_name', k): k for k, v in SACCTLOG_JOB_FIELDS.items()}

SACCTLOG_FIELD_NAME = ('jobid', 'jobidraw', 'cluster', 'partition', 'account', 'group', 'gid', 'user', 'uid',
                       'submit', 'eligible', 'start', 'end', 'elapsed', 'exitcode', 'state', 'nnodes', 'ncpus',
                       'reqcpus', 'reqmem',
                       'reqtres', 'alloctres', 'timelimit', 'nodelist', 'jobname')
SACCTLOG_FIELD_NAME_INT = tuple((SACCTLOG_NAME_TO_SLURM_INT[v] for v in SACCTLOG_FIELD_NAME))


class JobSacctLog:
    """Job from sacct log"""
    def __init__(self, **kwargs):
        self.jobid_str = ''
        self.jobid_raw_str = ''
        self.cluster = ''
        self.partition = ''
        self.account = ''
        self.group = ''
        self.gid = -1
        self.user = ''
        self.uid = -1
        self.submit = datetime.datetime(1, 1, 1, 0, 0)
        self.eligible = datetime.datetime(1, 1, 1, 0, 0)
        self.start = datetime.datetime(1, 1, 1, 0, 0)
        self.end = datetime.datetime(1, 1, 1, 0, 0)
        self.elapsed = datetime.timedelta(0)
        self.exitcode = ''
        self.state = ''
        self.nnodes = -1
        self.ncpus = -1
        self.req_cpus = -1
        self.req_mem = ''
        self.req_tres = ''
        self.alloc_tres = ''
        self.timelimit = datetime.timedelta(0)
        self.nodelist = ''
        self.jobname = ''

        for k,v in kwargs.items():
            if k not in SACCTLOG_JOB_FIELDS:
                raise ValueError(f"{k} unknown key (internal format) for sacct log entry")
            if SACCTLOG_JOB_FIELDS[k]['convert'] is slurm_datetime and v=='Unknown':
                self.__setattr__(k, None)
            else:
                self.__setattr__(k, SACCTLOG_JOB_FIELDS[k]['convert'](v))

    @staticmethod
    def from_line(line):
        fields = SlurmFileParser.split_nfields(line, len(SACCTLOG_FIELD_NAME))
        return JobSacctLog(**dict(zip(SACCTLOG_FIELD_NAME_INT, fields)))

    def __eq__(self, other):
        for k in SACCTLOG_JOB_FIELDS.keys():
            left = getattr(self, k)
            right = getattr(other, k)
            if getattr(self, k) != getattr(other, k):
                return False
        return True


class JobsListSacctLog:
    def __init__(self):
        self.jobs_list = []  # type: List[JobSacctLog]

    def parse_sacct_log(self, lines, processes=None):
        from slurmanalyser.utils import print_progress_bar

        log.info("Parsing sacct log file...")
        with mp.Pool(processes) as pool:
            self.jobs_list = list(tqdm.tqdm(pool.imap(JobSacctLog.from_line, lines, chunksize=1000), total=len(lines), file=sys.stdout))

        log.info("Done")

    @staticmethod
    def from_file(filename: str, processes: int = None) -> "JobsListSacctLog":
        jobs_list = JobsListSacctLog()

        def parse_sacclog(filename, nsplits):
            with open(filename) as f:
                for line in f:
                     yield line.rstrip().split("|", maxsplit=nsplits)

        # build the generator
        df = pd.DataFrame(
            parse_sacclog(filename, len(SACCTLOG_JOB_FIELDS)-1),
            columns=SACCTLOG_JOB_FIELDS.keys())

        # convert datetimes
        for col_time in ('submit', 'eligible', 'start', 'end'):
            n_unk = np.sum(df[col_time] == 'Unknown')
            if n_unk > 0:
                log.info(f"column {col_time}, {n_unk} records with value 'Unknown' converted to NaT")
            df.loc[df[col_time] == 'Unknown', col_time] = 'NaT'
            df[col_time] = pd.to_datetime(df[col_time])

        jobs_list.df = df
        return jobs_list


        from slurmanalyser.slurmparser import SlurmFileParser

        lines = SlurmFileParser.read_lines_from_file(filename)
        jobs_list = JobsListSacctLog()
        log.info(f"Reading sacct log from {filename}")
        jobs_list.parse_sacct_log(lines, processes=processes)
        return jobs_list
