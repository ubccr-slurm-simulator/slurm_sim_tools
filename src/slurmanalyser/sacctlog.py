import datetime
from typing import Sequence

from slurmanalyser.slurmparser import slurm_datetime, SlurmDuration, SlurmMemory
from slurmanalyser.slurmparser import SlurmFileParser
import slurmsim.log as log
import multiprocessing as mp
import os
import sys
import tqdm
import numpy as np
import pandas as pd
import re

from slurmanalyser.utils import get_file_open, SUPPORTED_COMPRESSION

import array





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


re_duration_str = r"(?:\d+:\d{2}:\d{2}|\d+-\d+:\d{2}:\d{2}|\d{1,2}:\d{2})"
re_duration_fraq_str = r"(?:\d+:\d{2}:\d{2}|\d+-\d+:\d{2}:\d{2}|\d{1,2}:\d{2})(?:\.[0-9]*)?"
re_datetime_str = r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}"
re_dur_unk_str = r"(?:\d+:\d{2}:\d{2}|\d+-\d+:\d{2}:\d{2}|\d{1,2}:\d{2}|Unknown)"
re_dur_empty_str = r"(?:\d+:\d{2}:\d{2}|\d+-\d+:\d{2}:\d{2}|\d{1,2}:\d{2}|)"
re_dur_partlim_empty_str = r"(?:\d+:\d{2}:\d{2}|\d+-\d+:\d{2}:\d{2}|\d{1,2}:\d{2}|Partition_Limit|)"
re_dur_empty_unk_str = r"(?:\d+:\d{2}:\d{2}|\d+-\d+:\d{2}:\d{2}|\d{1,2}:\d{2}|Unknown|)"
re_dur_empty_invalid_str = r"(?:\d+:\d{2}:\d{2}|\d+-\d+:\d{2}:\d{2}|\d{1,2}:\d{2}|INVALID|)"
re_datetime_unk_str = r"(?:\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}|Unknown)"
re_datetime_empty_unk_str = r"(?:\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}|Unknown|)"
re_exitcode_str = r"\d+:\d+"
re_exitcode_empty_str = r"(?:\d+:\d+|)"
re_digits_empty_str = r"(?:[0-9]+|)"
re_digits_partlim_empty_str = r"(?:[0-9]+|Partition_Limit|)"
re_digits_unk_str = r"(?:[0-9]+|Unknown)"
re_digits_str = r"[0-9]+"
re_any_nospec_str = r"[^|\n]*"
re_any_str = r".*"
re_alphanum_str = r"\w*"
re_alphanum2_str = r"[a-zA-Z0-9_-]*"
re_float_si_empty_str = r"(?:0|[0-9.]+[KMGTPE]|)"
re_float_siopt_empty_str = r"(?:[0-9.]+|[0-9.]+[KMGTPE]|)"
re_mem_str = r"[0-9.]+[KMGTPE][cn]?"
re_mem_question_str = r"[0-9.]+[KMGTPE?][cn]?"
re_mem_empty_str = r"(?:|[0-9.]+[KMGTPE][cn]?)"
re_mem_unk_empty_str = r"(?:|[0-9.]+[KMGTPE][cn]?|Unknown)"
re_empty_str = r"\s*"
re_empty_unk_str = r"(?:\s*|Unknown)"
re_dict_str = r"[^|\n]*"  # placeholder for a=1,b=2 values

re_duration = re.compile(re_duration_str)
re_datetime = re.compile(re_datetime_str)
re_dur_unk = re.compile(re_dur_unk_str)
re_dur_empty_unk = re.compile(re_dur_empty_unk_str)
re_datetime_unk = re.compile(re_datetime_unk_str)
re_datetime_empty_unk = re.compile(re_datetime_empty_unk_str)
re_exitcode = re.compile(re_exitcode_str)
re_exitcode_empty = re.compile(re_exitcode_empty_str)
re_digits_empty = re.compile(re_digits_empty_str)

from slurmanalyser.utils import util_to_int, util_factorize,util_to_str, util_norm_si, util_memory, default_na_is
from slurmanalyser.utils import util_to_str_unk, util_slurm_duration_to_duration, util_slurm_datetime_to_datetime

util_to_tresspec = lambda x, check_na='warning': x  # TResSpecs.from_string


# convert will convert col to col
# convert_flatten will convert to multiple columns
#
col_props = {
    'Account': {'pattern': re_alphanum2_str, 'convert': util_factorize},
    'AdminComment': {'pattern': re_any_nospec_str, 'convert': util_factorize},
    'AllocCPUS': {'pattern': re_digits_empty_str, 'convert': util_to_int},
    'AllocNodes': {'pattern': re_digits_empty_str, 'convert': util_to_int},
    'AllocTRES': {'pattern': re_dict_str, 'convert123': util_to_tresspec, 'convert_flatten': 'todo'},
    'AssocID': {'pattern': re_digits_empty_str, 'convert': util_to_int},
    'AveCPU': {'pattern': re_dur_empty_str, 'convert': util_slurm_duration_to_duration},  # Average (system + user) CPU time of all tasks in job.
    'AveCPUFreq': {'pattern': re_float_si_empty_str, 'convert': util_norm_si, 'units': 'Hz'},
    'AveDiskRead': {'pattern': re_float_si_empty_str, 'convert': util_norm_si},
    'AveDiskWrite': {'pattern': re_float_si_empty_str, 'convert': util_norm_si},
    'AvePages': {'pattern': re_float_si_empty_str, 'convert': util_norm_si},
    'AveRSS': {'pattern': re_float_siopt_empty_str, 'convert': util_norm_si},
    'AveVMSize': {'pattern': re_float_siopt_empty_str, 'convert': util_norm_si},
    'BlockID': {'pattern': re_any_nospec_str, 'convert': util_factorize},
    'Cluster': {'pattern': re_alphanum2_str, 'convert': util_factorize},
    'Comment': {'pattern': re_any_nospec_str, 'convert': util_factorize},
    'Constraints': {'pattern': re_any_str, 'convert': util_to_str, 'can_have_pipe_symbol':True},
    'Container': {'pattern': re_any_nospec_str, 'convert': util_factorize},
    'ConsumedEnergy': {'pattern': re_digits_empty_str, 'convert': util_to_int},
    'ConsumedEnergyRaw': {'pattern': re_digits_empty_str, 'convert': util_to_int},
    'CPUTime': {'pattern': re_duration_str, 'convert': util_slurm_duration_to_duration},
    'CPUTimeRAW': {'pattern': re_digits_str, 'convert': util_to_int},
    'DBIndex': {'pattern': re_digits_str, 'convert': util_to_int},
    'DerivedExitCode': {'pattern': re_exitcode_empty_str, 'convert': util_factorize},
    'Elapsed': {'pattern': re_duration_str, 'convert': util_slurm_duration_to_duration},
    'ElapsedRaw': {'pattern': re_digits_str, 'convert': util_to_int},
    'Eligible': {'pattern': re_datetime_unk_str, 'convert': util_slurm_datetime_to_datetime},
    'End': {'pattern': re_datetime_unk_str, 'convert': util_slurm_datetime_to_datetime},
    'ExitCode': {'pattern': re_exitcode_empty_str, 'convert': util_factorize},
    'Flags': {'pattern': re_any_nospec_str, 'convert': util_factorize},
    'GID': {'pattern': re_digits_empty_str, 'convert': util_to_int},
    'Group': {'pattern': re_alphanum2_str, 'convert': util_factorize},
    'JobID': {'pattern': re_any_nospec_str, 'convert': util_to_str},
    'JobIDRaw': {'pattern': re_any_nospec_str, 'convert123': util_to_str},
    'JobName': {'pattern': re_any_str, 'convert': util_to_str, 'can_have_pipe_symbol':True},
    'Layout': {'pattern': re_any_nospec_str, 'convert': util_to_str_unk},
    'MaxDiskRead': {'pattern': re_float_si_empty_str, 'convert': util_norm_si},
    'MaxDiskReadNode': {'pattern': re_alphanum2_str, 'convert': util_factorize},
    'MaxDiskReadTask': {'pattern': re_digits_empty_str, 'convert': util_to_int},
    'MaxDiskWrite': {'pattern': re_float_si_empty_str, 'convert': util_norm_si},
    'MaxDiskWriteNode': {'pattern': re_alphanum2_str, 'convert': util_factorize},
    'MaxDiskWriteTask': {'pattern': re_digits_empty_str, 'convert': util_to_int},
    'MaxPages': {'pattern': re_float_si_empty_str, 'convert': util_norm_si},
    'MaxPagesNode': {'pattern': re_alphanum2_str, 'convert': util_factorize},
    'MaxPagesTask': {'pattern': re_digits_empty_str, 'convert': util_to_int},
    'MaxRSS': {'pattern': re_float_si_empty_str, 'convert': util_norm_si},
    'MaxRSSNode': {'pattern': re_alphanum2_str, 'convert': util_factorize},
    'MaxRSSTask': {'pattern': re_digits_empty_str, 'convert': util_to_int},
    'MaxVMSize': {'pattern': re_float_si_empty_str, 'convert': util_norm_si},
    'MaxVMSizeNode': {'pattern': re_alphanum2_str, 'convert': util_factorize},
    'MaxVMSizeTask': {'pattern': re_digits_empty_str, 'convert': util_to_int},
    'McsLabel': {'pattern': re_any_nospec_str, 'convert': util_factorize},
    'MinCPU': {'pattern': re_dur_empty_str, 'convert': util_slurm_duration_to_duration},
    'MinCPUNode': {'pattern': re_alphanum2_str, 'convert': util_factorize},
    'MinCPUTask': {'pattern': re_digits_empty_str, 'convert': util_to_int},
    'NCPUS': {'pattern': re_digits_str, 'convert': util_to_int},
    'NNodes': {'pattern': re_digits_str, 'convert': util_to_int},
    'NodeList': {'pattern': re_any_nospec_str, 'convert': util_to_str},
    'NTasks': {'pattern': re_digits_empty_str, 'convert': util_to_int},
    'Priority': {'pattern': re_digits_empty_str, 'convert': util_to_int},
    'Partition': {'pattern': re_any_nospec_str, 'convert': util_factorize},
    'QOS': {'pattern': re_any_nospec_str, 'convert': util_factorize},
    'QOSRAW': {'pattern': re_digits_empty_str, 'convert': util_to_int},
    'Reason': {'pattern': re_any_nospec_str, 'convert': util_factorize},
    'ReqCPUFreq': {'pattern': re_digits_unk_str, 'convert': util_to_int},
    'ReqCPUFreqMin': {'pattern': re_digits_unk_str, 'convert': util_to_int},
    'ReqCPUFreqMax': {'pattern': re_digits_unk_str, 'convert': util_to_int},
    'ReqCPUFreqGov': {'pattern': re_digits_unk_str, 'convert': util_to_int},
    'ReqCPUS': {'pattern': re_digits_str, 'convert': util_to_int},
    'ReqMem': {'pattern': re_mem_question_str, 'convert123': SlurmMemory.from_string},
    'ReqNodes': {'pattern': re_digits_str, 'convert': util_to_int},
    'ReqTRES': {'pattern': re_dict_str, 'convert': util_to_tresspec},
    'Reservation': {'pattern': re_empty_str, 'convert': util_factorize},
    'ReservationId': {'pattern': re_digits_empty_str, 'convert': util_to_int},
    'Reserved': {'pattern': re_dur_empty_invalid_str, 'convert': util_slurm_duration_to_duration},
    'ResvCPU': {'pattern': re_dur_empty_invalid_str, 'convert': util_slurm_duration_to_duration},
    'ResvCPURAW': {'pattern': re_digits_empty_str, 'convert': util_to_int},
    'Start': {'pattern': re_datetime_empty_unk_str, 'convert': util_slurm_datetime_to_datetime},
    'State': {'pattern': re_any_nospec_str, 'convert': util_factorize},
    'Submit': {'pattern': re_datetime_str, 'convert': util_slurm_datetime_to_datetime},
    'SubmitLine': {'pattern': re_any_str, 'convert': util_to_str, 'can_have_pipe_symbol':True},
    'Suspended': {'pattern': re_duration_str, 'convert': util_slurm_duration_to_duration},
    'SystemCPU': {'pattern': re_duration_fraq_str, 'convert': util_slurm_duration_to_duration},
    'SystemComment': {'pattern': re_any_nospec_str, 'convert': util_factorize},
    'Timelimit': {'pattern': re_dur_partlim_empty_str, 'convert':
        lambda v, check_na='ignore': util_slurm_duration_to_duration(v, check_na=check_na, na_is=default_na_is+['Partition_Limit'])}, #default timelimit is Partition_Limit
    'TimelimitRaw': {'pattern': re_digits_partlim_empty_str, 'convert':
        lambda v, check_na='ignore': util_to_int(v, check_na=check_na, na_is=default_na_is+['Partition_Limit'])},
    'TotalCPU': {'pattern': re_duration_fraq_str, 'convert': util_slurm_duration_to_duration},
    'TRESUsageInAve': {'pattern': re_dict_str, 'convert': util_to_str},
    'TRESUsageInMax': {'pattern': re_dict_str, 'convert': util_to_str},
    'TRESUsageInMaxNode': {'pattern': re_dict_str, 'convert': util_to_str},
    'TRESUsageInMaxTask': {'pattern': re_dict_str, 'convert': util_to_str},
    'TRESUsageInMin': {'pattern': re_dict_str, 'convert': util_to_str},
    'TRESUsageInMinNode': {'pattern': re_dict_str, 'convert': util_to_str},
    'TRESUsageInMinTask': {'pattern': re_dict_str, 'convert': util_to_str},
    'TRESUsageInTot': {'pattern': re_dict_str, 'convert': util_to_str},
    'TRESUsageOutAve': {'pattern': re_dict_str, 'convert': util_to_str},
    'TRESUsageOutMax': {'pattern': re_dict_str, 'convert': util_to_str},
    'TRESUsageOutMaxNode': {'pattern': re_dict_str, 'convert': util_to_str},
    'TRESUsageOutMaxTask': {'pattern': re_dict_str, 'convert': util_to_str},
    'TRESUsageOutMin': {'pattern': re_dict_str, 'convert': util_to_str},
    'TRESUsageOutMinNode': {'pattern': re_dict_str, 'convert': util_to_str},
    'TRESUsageOutMinTask': {'pattern': re_dict_str, 'convert': util_to_str},
    'TRESUsageOutTot': {'pattern': re_dict_str, 'convert': util_to_str},
    'UID': {'pattern': re_digits_empty_str, 'convert': util_to_int},
    'User': {'pattern': re_any_nospec_str, 'convert': util_factorize},
    'UserCPU': {'pattern': re_duration_fraq_str, 'convert': util_slurm_duration_to_duration},
    'WCKey': {'pattern': re_any_nospec_str, 'convert': util_factorize},
    'WCKeyID': {'pattern': re_digits_empty_str, 'convert': util_to_int},
    'WorkDir': {'pattern': re_any_nospec_str, 'convert': util_factorize},
}

def convert_jobid_raw(df):
    # format:
    # if JOB or JOBCOMP then integer
    # if jobstep
    #       .batch SLURM_BATCH_SCRIPT
    #       .extern SLURM_EXTERN_CONT
    #       .%u step id
    pass


ConsumedEnergy_ExitCode = re.compile("\|".join((col_props[c]['pattern'] for c in ('ConsumedEnergy', 'ConsumedEnergyRaw', 'CPUTime', 'CPUTimeRAW', 'DBIndex', 'DerivedExitCode',
'Elapsed', 'ElapsedRaw', 'Eligible', 'End', 'ExitCode'))))

# essentially corresponds to year and month with column order showed up
columns_formats = {
    'dump_2101': [
        'Account', 'AdminComment', 'AllocCPUS', 'AllocNodes', 'AllocTRES', 'AssocID', 'AveCPU', 'AveCPUFreq',
        'AveDiskRead', 'AveDiskWrite',
        'AvePages', 'AveRSS', 'AveVMSize', 'BlockID', 'Cluster', 'Comment', 'Constraints', 'ConsumedEnergy',
        'ConsumedEnergyRaw', 'CPUTime',
        'CPUTimeRAW', 'DBIndex', 'DerivedExitCode', 'Elapsed', 'ElapsedRaw', 'Eligible', 'End', 'ExitCode', 'Flags',
        'GID', 'Group', 'JobID',
        'JobIDRaw', 'JobName', 'Layout', 'MaxDiskRead', 'MaxDiskReadNode', 'MaxDiskReadTask', 'MaxDiskWrite',
        'MaxDiskWriteNode',
        'MaxDiskWriteTask', 'MaxPages', 'MaxPagesNode', 'MaxPagesTask', 'MaxRSS', 'MaxRSSNode', 'MaxRSSTask',
        'MaxVMSize', 'MaxVMSizeNode',
        'MaxVMSizeTask', 'McsLabel', 'MinCPU', 'MinCPUNode', 'MinCPUTask', 'NCPUS', 'NNodes', 'NodeList', 'NTasks',
        'Priority', 'Partition',
        'QOS', 'QOSRAW', 'Reason', 'ReqCPUFreq', 'ReqCPUFreqMin', 'ReqCPUFreqMax', 'ReqCPUFreqGov', 'ReqCPUS',
        'ReqMem', 'ReqNodes', 'ReqTRES', 'Reservation', 'ReservationId', 'Reserved', 'ResvCPU',
        'ResvCPURAW', 'Start', 'State', 'Submit', 'Suspended', 'SystemCPU', 'SystemComment', 'Timelimit',
        'TimelimitRaw', 'TotalCPU', 'TRESUsageInAve', 'TRESUsageInMax', 'TRESUsageInMaxNode',
        'TRESUsageInMaxTask', 'TRESUsageInMin', 'TRESUsageInMinNode', 'TRESUsageInMinTask', 'TRESUsageInTot',
        'TRESUsageOutAve', 'TRESUsageOutMax', 'TRESUsageOutMaxNode', 'TRESUsageOutMaxTask',
        'TRESUsageOutMin', 'TRESUsageOutMinNode', 'TRESUsageOutMinTask', 'TRESUsageOutTot', 'UID', 'User', 'UserCPU',
        'WCKey', 'WCKeyID', 'WorkDir'],
    'dump_2110': [
        'Account', 'AdminComment', 'AllocCPUS', 'AllocNodes', 'AllocTRES', 'AssocID', 'AveCPU', 'AveCPUFreq',
        'AveDiskRead', 'AveDiskWrite', 'AvePages', 'AveRSS', 'AveVMSize', 'BlockID', 'Cluster', 'Comment',
        'Constraints',
        'Container', 'ConsumedEnergy', 'ConsumedEnergyRaw', 'CPUTime', 'CPUTimeRAW', 'DBIndex', 'DerivedExitCode',
        'Elapsed', 'ElapsedRaw', 'Eligible', 'End', 'ExitCode', 'Flags', 'GID', 'Group', 'JobID', 'JobIDRaw',
        'JobName',
        'Layout', 'MaxDiskRead', 'MaxDiskReadNode', 'MaxDiskReadTask', 'MaxDiskWrite', 'MaxDiskWriteNode',
        'MaxDiskWriteTask', 'MaxPages', 'MaxPagesNode', 'MaxPagesTask', 'MaxRSS', 'MaxRSSNode', 'MaxRSSTask',
        'MaxVMSize', 'MaxVMSizeNode', 'MaxVMSizeTask', 'McsLabel', 'MinCPU', 'MinCPUNode', 'MinCPUTask', 'NCPUS',
        'NNodes', 'NodeList', 'NTasks', 'Priority', 'Partition', 'QOS', 'QOSRAW', 'Reason', 'ReqCPUFreq',
        'ReqCPUFreqMin',
        'ReqCPUFreqMax', 'ReqCPUFreqGov', 'ReqCPUS', 'ReqMem', 'ReqNodes', 'ReqTRES', 'Reservation',
        'ReservationId', 'Reserved', 'ResvCPU', 'ResvCPURAW', 'Start', 'State', 'Submit', 'SubmitLine', 'Suspended',
        'SystemCPU', 'SystemComment', 'Timelimit', 'TimelimitRaw', 'TotalCPU', 'TRESUsageInAve', 'TRESUsageInMax',
        'TRESUsageInMaxNode', 'TRESUsageInMaxTask', 'TRESUsageInMin', 'TRESUsageInMinNode', 'TRESUsageInMinTask',
        'TRESUsageInTot', 'TRESUsageOutAve', 'TRESUsageOutMax', 'TRESUsageOutMaxNode', 'TRESUsageOutMaxTask',
        'TRESUsageOutMin', 'TRESUsageOutMinNode', 'TRESUsageOutMinTask', 'TRESUsageOutTot', 'UID', 'User',
        'UserCPU', 'WCKey', 'WCKeyID', 'WorkDir'],
    'xdmod1': [
        'JobID', 'JobIDRaw', 'Cluster', 'Partition', 'Account', 'Group', 'GID', 'User', 'UID', 'Submit', 'Eligible',
        'Start', 'End', 'Elapsed', 'ExitCode', 'State', 'NNodes', 'NCPUS', 'ReqCPUS', 'ReqMem', 'ReqTRES',
        'AllocTRES', 'Timelimit', 'NodeList', 'JobName']
}


class SacctLog:
    def __init__(self):
        self.df = pd.DataFrame()  # type pd.DataFrame

    def convert_columns(self, check_na='warning'):
        """convert string columns"""
        for col in self.df:
            if col in col_props:
                if 'convert_flatten' in col_props[col] and col_props[col]['convert_flatten'] != 'todo':
                    pass
                if 'convert' in col_props[col] and col_props[col]['convert'] != 'todo':
                    convert = col_props[col]['convert']
                    if convert == util_to_str:
                        convert = None
                    if self.df[col].dtype != np.object:
                        convert = None
                        log.debug2(f"{col} is already not np.object")
                    if convert is not None:
                        log.debug2(f"converting {col} using {col_props[col]['convert'].__name__}")
                        self.df[col] = col_props[col]['convert'](self.df[col], check_na=check_na)
        if 'ReqMem' in self.df:
            x, c = util_memory(self.df['ReqMem'], check_na=check_na)
            self.df['ReqMem'] = x
            self.df.insert(self.df.columns.get_loc('ReqMem') + 1, 'ReqMemPerCore', c)

    def keep_scheduling_related(self):
        scheduling_related_cols = [
            'Account', 'AllocCPUS', 'AllocNodes', 'AllocTRES', 'Cluster',
            'Constraints',
            'Elapsed', 'ElapsedRaw', 'Eligible', 'End', 'Group', 'JobID', 'JobIDRaw',
            'JobName',
            'NCPUS',
            'NNodes', 'NodeList', 'NTasks', 'Priority', 'Partition', 'QOS', 'Reason', 'ReqCPUS', 'ReqMem', 'ReqNodes', 'ReqTRES',
            'Reservation',
            'ReservationId', 'Reserved', 'ResvCPU', 'Start', 'State', 'Submit', 'SubmitLine',
            'Timelimit', 'TimelimitRaw',
            'User']

        self.df = self.df[[c for c in scheduling_related_cols if c in self.df]]

    def simplify_state(self):
        """
        CANCELLED by 89200751 -> CANCELLED
        @return: None
        """
        if 'State' in self.df:
            self.df['State'].loc[self.df['State'].str.count('CANCELLED') > 0] = 'CANCELLED'

    def append(self, other):
        df = self.df.append(other.df,ignore_index=True)
        df.drop_duplicates(subset=['JobIDRaw', 'Submit', 'Start'], keep='last', inplace=True, ignore_index=True)
        self.df = df

    def generate_nodeusage(self):
        """
        Return and set sacctlog.nodeusage where index is index from self.df and value is node name
        @return:
        """
        if 'NodeList' not in self.df:
            log.error("NodeList not in self.df")
            return

        import array
        from hostlist import expand_hostlist

        hosts_dict = {"None": 0}

        job_recid = array.array('l')
        node_id = array.array('l')

        for index, hosts in self.df['NodeList'].items():
            if hosts == 'None assigned':
                continue
            for host in expand_hostlist(hosts):
                if host not in hosts_dict:
                    hosts_dict[host] = len(hosts_dict)
                job_recid.append(index)
                node_id.append(hosts_dict[host])

        self.nodeusage = pd.Series(
            pd.Categorical.from_codes(codes=node_id,categories=hosts_dict.keys()),
            index=job_recid)
        return self.nodeusage

    def to_feather(self, filename, compression=None, compression_level=19):
        import os
        if compression == "zstd" or os.path.splitext(filename)[-1] in ('.zstd', '.zst'):
            self.df.to_feather(filename, compression="zstd", compression_level=compression_level)
        elif compression is not None:
            self.df.to_feather(filename, compression=compression, compression_level=compression_level)
        else:
            self.df.to_feather(filename)

    @classmethod
    def read_feather(cls, filename):
        sacctlog = cls()
        sacctlog.df = pd.read_feather(filename)
        #sacctlog.df.drop('index', axis=1, inplace=True)
        return sacctlog

    def to_parquet(self, filename):
        raise NotImplementedError("not supported yet due to timedelta lack in parquet")
        self.df.to_parquet(filename)

    @classmethod
    def read_parquet(cls, filename):
        sacctlog = cls()
        sacctlog.df = pd.read_parquet(filename)
        return sacctlog

    @classmethod
    def read_logfile(cls, filename: str, columns: Sequence[str] = None,
                     header: bool = True, col_format: str = None, convert_data: bool = True, check_na='warning',
                     skip_jobsteps: bool = True, keep_scheduling_related=False, simplify_state=True) -> 'SacctLog':
        """
        Read sacct log from file. File can be compressed, this is identified by extension.


        @param filename:
        @param col_format:  column formats recognizable strings: dump1, xdmod1
        @param columns: column names in file
        @param header: is header present in file
        @param convert_data: convert string to proper data formats
        @return: SacctLog
        """
        if not skip_jobsteps:
            raise NotImplementedError("can not handle job steps yet")
        if columns is None and col_format is not None:
            columns = columns_formats[col_format]

        if columns is None:
            columns = cls.get_colnames_from_sacclog(filename)

        sacctlog = cls()
        sacctlog.df = cls.get_init_sacctlog_df(filename, columns=columns, header=header)

        if keep_scheduling_related:
            sacctlog.keep_scheduling_related()

        if simplify_state:
            sacctlog.simplify_state()

        if skip_jobsteps:
            sacctlog.df = sacctlog.df.loc[~sacctlog.df['JobIDRaw'].str.contains(".", regex=False)]
            sacctlog.df['JobIDRaw'] = util_to_int(sacctlog.df['JobIDRaw'])
            sacctlog.df.reset_index(inplace=True, drop=True)

        if convert_data:
            sacctlog.convert_columns(check_na=check_na)

        return sacctlog

    @staticmethod
    def get_colnames_from_sacclog(filename):
        m_open = get_file_open(filename)
        with m_open(filename, 'rt') as fin:
            line = next(fin).rstrip()
            colnames = line.split("|")
        return colnames

    @staticmethod
    def parse_sacclog_iter_generic(filename, columns=None, header=True):
        """This is generic sacct log processor and only can handle | in the jobname"""
        m_open = get_file_open(filename)

        # newline = '\n' is importent because some jobs contains \r and universal new line treat it as a new line
        with m_open(filename, 'rt', newline = '\n') as fin:
            if header:
                line = next(fin).rstrip()
                if columns is not None and  columns != line.split("|"):
                    raise ValueError("Column names do not match one in file!")

            ncols = len(columns)
            col_pos = array.array('l', [0] * (ncols + 1))

            # assume only  JobName can contain |
            icol_jobname = columns.index("JobName")

            for line in fin:
                # no | in comment or jobname
                extra_pipe = line.count("|") - ( ncols - 1 )
                if extra_pipe == 0:
                    yield line.rstrip().split("|")
                    continue

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

    @staticmethod
    def parse_sacclog_iter_dump2110(filename, columns=None, header=True):
        """
        process dump1 format can recognize | in constrains, job names and SubmitLine
        @param filename:
        @param columns:
        @param header:
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

        if columns is not None and columns != columns_formats['dump_2110']:
            raise ValueError("Column names do not match one in file!")
        if columns is None:
            columns = columns_formats['dump_2110']

        m_open = get_file_open(filename)

        # newline = '\n' is importent because some jobs contains \r and universal new line treat it as a new line
        with m_open(filename, 'rt', newline = '\n') as fin:
            if header:
                line = next(fin).rstrip()
                if columns != line.split("|"):
                    raise ValueError("Column names do not match one in file!")

            iline = 1
            ncols = len(columns)
            col_pos = array.array('l', [0] * (ncols + 1))

            # dump2101 columns Constraint, JobName and SubmitLine can contain |
            log.debug("coloumn format: dump2110")

            icol_constraints = columns.index("Constraints")
            icol_jobname = columns.index("JobName")
            icol_submitline = columns.index("SubmitLine")
            iConsumedEnergy = columns.index("ConsumedEnergy")
            iExitCode = columns.index("ExitCode")

            iNCPUS = columns.index('NCPUS')
            iNNodes = columns.index('NNodes')
            iStart = columns.index('Start')
            iSubmit = columns.index('Submit')

            reNCPUS = re.compile(col_props['NCPUS']['pattern'])
            reNNodes = re.compile(col_props['NNodes']['pattern'])
            reStart = re.compile(col_props['Start']['pattern'])
            reSubmit = re.compile(col_props['Submit']['pattern'])

            for line in fin:
                # no | in comment or jobname
                extra_pipe = line.count("|") - (ncols-1)
                iline += 1
                if extra_pipe < 0:
                    # i.e. new line in one of the fields
                    while extra_pipe < 0:
                        line = line.rstrip() + next(fin)
                        extra_pipe = line.count("|") - (ncols - 1)
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

                # identify | in constrains
                i_start = i
                ipos_start = ipos
                pipe_removed = 0
                while True:
                    while i <= icol_jobname:
                        i += 1
                        ipos = line.find("|", ipos + 1)
                        col_pos[i] = ipos
                    # the above need to be redone untill some types of field matches

                    match = bool(ConsumedEnergy_ExitCode.fullmatch(line, col_pos[iConsumedEnergy] + 1, col_pos[iExitCode + 1]))

                    if match:
                        break
                    elif pipe_removed >= extra_pipe:
                        fields = [line[col_pos[i] + 1:col_pos[i + 1]] for i in range(ncols)]
                        print("can not read, too many |")

                        print(f"line: {iline}, found: {line.count('|') + 1} |, expect {ncols} columns", match)
                        print(line)
                        for k, v in zip(columns, fields):
                            print(f"{k}=|{v}|")
                        raise ValueError("can not read, too many |")
                    else:
                        pipe_removed += 1
                        i = i_start
                        ipos = line.find("|", ipos_start + 1)
                        ipos_start = ipos
                # identify | in job name
                i -= 1
                ipos = col_pos[i]
                i_start = i
                ipos_start = ipos
                while True:
                    while i <= icol_submitline:
                        i += 1
                        ipos = line.find("|", ipos + 1)
                        col_pos[i] = ipos
                    # the above need to be redone untill some types of field matches

                    match = bool(reNCPUS.fullmatch(line, col_pos[iNCPUS] + 1, col_pos[iNCPUS + 1])) and \
                            bool(reNNodes.fullmatch(line, col_pos[iNNodes] + 1, col_pos[iNNodes + 1])) and \
                            bool(reStart.fullmatch(line, col_pos[iStart] + 1, col_pos[iStart + 1])) and \
                            bool(reSubmit.fullmatch(line, col_pos[iSubmit] + 1, col_pos[iSubmit + 1]))

                    if match:
                        break
                    elif pipe_removed >= extra_pipe:
                        fields = [line[col_pos[i] + 1:col_pos[i + 1]] for i in range(ncols)]
                        print("can not read, too many |")

                        print(iline, line.count("|") + 1, ncols, match)
                        print(line)
                        for k, v in zip(columns, fields):
                            print(f"{k}=|{v}|")
                        raise ValueError("can not read, too many |")
                    else:
                        pipe_removed += 1
                        i = i_start
                        ipos = line.find("|", ipos_start + 1)
                        ipos_start = ipos
                #
                i = ncols
                ipos = len(line) - 1
                col_pos[i] = ipos
                while i > icol_submitline + 1:
                    i -= 1
                    ipos = line.rfind("|", 0, ipos)
                    col_pos[i] = ipos

                fields = [line[col_pos[i] + 1:col_pos[i + 1]] for i in range(ncols)]
                yield fields

    @staticmethod
    def parse_sacclog_iter_dump2101(filename, columns=None, header=True):
        """
        process dump1 format can recognize | in constrains and job names
        @param filename:
        @param columns:
        @param header:
        @return:
        """

        if columns is not None and columns != columns_formats['dump_2101']:
            raise ValueError("Column names do not match one in file!")
        if columns is None:
            columns = columns_formats['dump_2101']

        m_open = get_file_open(filename)
        # newline = '\n' is importent because some jobs contains \r and universal new line treat it as a new line
        with m_open(filename, 'rt', newline='\n') as fin:
            iline = 0
            if header:
                line = next(fin).rstrip()
                if columns != line.split("|"):
                    raise ValueError("Column names do not match one in file!")
                iline = 1
            ncols = len(columns)
            col_pos = array.array('l', [0] * (ncols + 1))

            # dump2101 columns Constraint and JobName can contain |
            log.debug("column format: dump2101")

            icol_constraints = columns.index("Constraints")
            icol_jobname = columns.index("JobName")
            iConsumedEnergy = columns.index("ConsumedEnergy")
            iExitCode = columns.index("ExitCode")

            iNCPUS = columns.index('NCPUS')
            iNNodes = columns.index('NNodes')
            iStart = columns.index('Start')
            iSubmit = columns.index('Submit')

            reNCPUS = re.compile(col_props['NCPUS']['pattern'])
            reNNodes = re.compile(col_props['NNodes']['pattern'])
            reStart = re.compile(col_props['Start']['pattern'])
            reSubmit = re.compile(col_props['Submit']['pattern'])

            for line in fin:
                # no | in comment or jobname
                line = line.strip()
                extra_pipe = line.count("|") - (ncols - 1)
                iline += 1
                if extra_pipe == 0:
                    yield line.split("|")
                    continue
                if line == '' or line[:1] == '#':
                    continue
                # positions to colmment
                i = 0
                ipos = -1
                col_pos[i] = ipos
                while i < icol_constraints:
                    i += 1
                    ipos = line.find("|", ipos + 1)
                    col_pos[i] = ipos


                # identify | in constrains
                i_start = i
                ipos_start = ipos
                pipe_removed = 0
                while True:
                    while i <= icol_jobname:
                        i += 1
                        ipos = line.find("|", ipos + 1)
                        col_pos[i] = ipos
                    # the above need to be redone untill some types of field matches

                    match = bool(
                        ConsumedEnergy_ExitCode.fullmatch(line, col_pos[iConsumedEnergy] + 1, col_pos[iExitCode + 1]))

                    if match:
                        break
                    elif pipe_removed >= extra_pipe:
                        fields = [line[col_pos[i] + 1:col_pos[i + 1]] for i in range(ncols)]
                        print("can not read, too many |")

                        print(f'line # {iline}, possible columns: {line.count("|") + 1}, actual columns: {ncols}, '
                              f'atches the mid pattern: {match}, line:')
                        print(line)
                        print("Current fields")
                        for k, v in zip(columns, fields):
                            print(f"{k}=|{v}|")
                        raise ValueError("can not read, too many |")
                    else:
                        pipe_removed += 1
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

    @classmethod
    def get_parse_sacclog_iter(cls, filename, columns=None):
        """
        return list of lists parsed from sacct logs, take care of | in JobNames as well as
        | in both Constraints and JobNames in certain dumps
        @param filename:
        @param columns:
        @return:
        """

        if columns is None:
            columns = cls.get_colnames_from_sacclog(filename)

        if columns == columns_formats['dump_2110']:
            return cls.parse_sacclog_iter_dump2110
        elif columns == columns_formats['dump_2101']:
            return cls.parse_sacclog_iter_dump2101
        else:
            return cls.parse_sacclog_iter_generic

    @classmethod
    def get_init_sacctlog_df(cls, filename, columns=None, header=True):
        import pandas
        if columns is None:
            columns = cls.get_colnames_from_sacclog(filename)
        df = pandas.DataFrame(
            cls.get_parse_sacclog_iter(filename)(filename, columns=columns, header=header),
            columns=columns)
        return df


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


class JobSacctLogOld:
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


class JobsListSacctLogOld:
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


def format_sacctlog(sacctlog, output=None, sep="|"):
    """

    @param sacctlog:
    @param output:
    @return: None
    """
    if output is None:
        # add _formatted to basename
        base,ext = os.path.splitext(sacctlog)
        if ext in SUPPORTED_COMPRESSION:
            base, ext2 = os.path.splitext(base)
            ext = f"{ext2}{ext}"
        output = f"{base}_formatted{ext}"

    log.debug(f"Reformat {sacctlog} to {output}")
    m_sacctlog = SacctLog.read_logfile(sacctlog)
    with get_file_open(output)(output,"w") as out:
        m_sacctlog.df.to_csv(out, index=False,sep=sep)
