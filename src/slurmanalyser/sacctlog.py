import datetime
from slurmanalyser.slurmparser import slurm_datetime, SlurmDuration, SlurmMemory
from slurmanalyser.slurmparser import SlurmFileParser
import logging as log
import multiprocessing as mp
import sys
import tqdm


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
        self.jobs_list = []

    def parse_sacct_log(self, lines, processes=None):
        from slurmanalyser.utils import print_progress_bar

        log.info("Parsing sacct log file...")
        with mp.Pool(processes) as pool:
            self.jobs_list = list(tqdm.tqdm(pool.imap(JobSacctLog.from_line, lines, chunksize=1000), total=len(lines), file=sys.stdout))

        log.info("Done")

    @staticmethod
    def from_file(filename: str, processes: int = None):
        from slurmanalyser.slurmparser import SlurmFileParser

        jobs_list = JobsListSacctLog()
        log.info(f"Reading sacct log from {filename}")
        lines = SlurmFileParser.read_lines_from_file(filename)
        jobs_list.parse_sacct_log(lines, processes=processes)
        return jobs_list
