import re
import datetime
# pretty capitalization of slurm conf
slurm_conf_keywords = {
    'accountingstorageenforce': 'AccountingStorageEnforce',
    'accountingstoragehost': 'AccountingStorageHost',
    'accountingstoragetres': 'AccountingStorageTRES',
    'accountingstoragetype': 'AccountingStorageType',
    'accountingstoreflags': 'AccountingStoreFlags',
    'acctgatherenergytype': 'AcctGatherEnergyType',
    'acctgathernodefreq': 'AcctGatherNodeFreq',
    'allocnodes': 'AllocNodes',
    'allowqos': 'AllowQOS',
    'authtype': 'AuthType',
    'clustername': 'ClusterName',
    'controlmachine': 'ControlMachine',
    'corespersocket': 'CoresPerSocket',
    'cpus': 'CPUs',
    'cryptotype': 'CryptoType',
    'default': 'Default',
    'defaulttime': 'DefaultTime',
    'defmempercpu': 'DefMemPerCPU',
    'enforcepartlimits': 'EnforcePartLimits',
    'epilog': 'Epilog',
    'fairsharedampeningfactor': 'FairShareDampeningFactor',
    'feature': 'Feature',
    'gres': 'Gres',
    'grestypes': 'GresTypes',
    'healthcheckinterval': 'HealthCheckInterval',
    'healthcheckprogram': 'HealthCheckProgram',
    'inactivelimit': 'InactiveLimit',
    'jobacctgatherfrequency': 'JobAcctGatherFrequency',
    'jobacctgatherparams': 'JobAcctGatherParams',
    'jobacctgathertype': 'JobAcctGatherType',
    'jobcomptype': 'JobCompType',
    'jobrequeue': 'JobRequeue',
    'killonbadexit': 'KillOnBadExit',
    'killwait': 'KillWait',
    'licenses': 'Licenses',
    'lln': 'LLN',
    'mailprog': 'MailProg',
    'maxnodes': 'MaxNodes',
    'maxstepcount': 'MaxStepCount',
    'maxtime': 'MaxTime',
    'messagetimeout': 'MessageTimeout',
    'minjobage': 'MinJobAge',
    'mpidefault': 'MpiDefault',
    'mpiparams': 'MpiParams',
    'nodename': 'NodeName',
    'nodes': 'Nodes',
    'partitionname': 'PartitionName',
    'preemptmode': 'PreemptMode',
    'preempttype': 'PreemptType',
    'priority': 'Priority',
    'prioritydecayhalflife': 'PriorityDecayHalfLife',
    'priorityfavorsmall': 'PriorityFavorSmall',
    'priorityflags': 'PriorityFlags',
    'prioritymaxage': 'PriorityMaxAge',
    'prioritytype': 'PriorityType',
    'priorityweightage': 'PriorityWeightAge',
    'priorityweightfairshare': 'PriorityWeightFairshare',
    'priorityweightjobsize': 'PriorityWeightJobSize',
    'priorityweightpartition': 'PriorityWeightPartition',
    'priorityweightqos': 'PriorityWeightQOS',
    'priorityweighttres': 'PriorityWeightTRES',
    'proctracktype': 'ProctrackType',
    'prolog': 'Prolog',
    'prologflags': 'PrologFlags',
    'propagateresourcelimits': 'PropagateResourceLimits',
    'qos': 'QOS',
    'realmemory': 'RealMemory',
    'rebootprogram': 'RebootProgram',
    'resumetimeout': 'ResumeTimeout',
    'returntoservice': 'ReturnToService',
    'schedulerparameters': 'SchedulerParameters',
    'schedulertype': 'SchedulerType',
    'selecttype': 'SelectType',
    'selecttypeparameters': 'SelectTypeParameters',
    'slurmctlddebug': 'SlurmctldDebug',
    'slurmctldlogfile': 'SlurmctldLogFile',
    'slurmctldparameters': 'SlurmctldParameters',
    'slurmctldport': 'SlurmctldPort',
    'slurmctldtimeout': 'SlurmctldTimeout',
    'slurmddebug': 'SlurmdDebug',
    'slurmdlogfile': 'SlurmdLogFile',
    'slurmdport': 'SlurmdPort',
    'slurmdspooldir': 'SlurmdSpoolDir',
    'slurmdtimeout': 'SlurmdTimeout',
    'slurmschedlogfile': 'SlurmSchedLogFile',
    'slurmuser': 'SlurmUser',
    'sockets': 'Sockets',
    'state': 'State',
    'statesavelocation': 'StateSaveLocation',
    'switchtype': 'SwitchType',
    'taskplugin': 'TaskPlugin',
    'taskprolog': 'TaskProlog',
    'threadspercore': 'ThreadsPerCore',
    'tmpfs': 'TmpFs',
    'topologyplugin': 'TopologyPlugin',
    'usepam': 'UsePAM',
    'vsizefactor': 'VSizeFactor',
    'waittime': 'Waittime',
    'weight': 'Weight'
}

sacctmgr_keywords = {
    'cluster': 'Cluster',
    'parent': 'Parent',
    'user': 'User',
    'account': 'Account',
    'description': 'Description',
    'organization': 'Organization',
    'defaultaccount': 'DefaultAccount',
    'fairshare': 'Fairshare',
    'adminlevel': 'AdminLevel',
    'defaultqos': 'DefaultQOS'
}

slurm_keywords = slurm_conf_keywords.copy()
slurm_keywords.update(sacctmgr_keywords)

slurm_convert_values = {
    'Fairshare': int
}

class SlurmFileParser:
    def __init__(self):
        # source lines
        self.lines = []

    @staticmethod
    def read_lines_from_file(filename: str, include_childs = True) -> list[str]:
        """
        Read lines from file if have line `include another_filename` includes lines inline from that file.
        :param filename:
        :param include_childs: include include files
        :return:
        """
        lines = []

        import os
        file_extention = os.path.splitext(filename)
        if file_extention==".xz":
            import lzma
            file_open = lzma.open
        elif file_extention == ".gz":
            import gzip
            file_open = gzip.open
        else:
            file_open = open

        with file_open(filename, "rt") as fout:
            for line in fout:
                line = line.rstrip("\n")
                if include_childs and re.match("^include",line.lower().strip()):
                    command, param = SlurmFileParser.split_expr(line, pretty_left=True, split=" ")
                    lines += SlurmFileParser._lines_from_file(param)
                else:
                    lines.append(line)
        return lines

    @staticmethod
    def split_expr(line:str, pretty_left=True, split="=", convert_values=False) -> tuple[str, str]:
        """return left, right from expression like left=right"""
        if line.count(split) == 0:
            raise ValueError(f"No split string: '{split}'!")
        i_equal = line.index(split)
        left = line[:i_equal].strip()

        if pretty_left:
            if left.lower() not in slurm_keywords:
                print(f"Warning:{left} not in slurm_keywords")
            left = slurm_keywords.get(left.lower(), left.lower())
        right = "" if len(line) < i_equal + 1 else line[i_equal + 1:].strip()

        if convert_values:
            right = right.strip("'").strip('"')
            if left in slurm_convert_values:
                right = slurm_convert_values[left](right)
            return left, right
        else:
            return left, right

    @staticmethod
    def split_expr_array(s:str, split=None, convert_values=False):
        "l1=r1 l2=r2 -> ((l1,r1),(l2,r2))"
        if split:
            return (SlurmFileParser.split_expr(s1, convert_values=convert_values) for s1 in s.split(split))
        else:
            return (SlurmFileParser.split_expr(s1, convert_values=convert_values) for s1 in s.split())

    @staticmethod
    def split_nfields(line:str, nfields=-1, split="|") -> tuple[str]:
        """
        Raise ValueError if nfields does not match to output
        :param line: line to split
        :param nfields: number of fields
        :param split: split symbols
        :return: list of fields
        """
        maxsplit = nfields - 1 if nfields >0 else -1
        line = line.strip("|\n")
        fields = line.split("|", maxsplit=maxsplit)

        if 0 < nfields != len(fields):
            raise ValueError(f"Number of fields in line ({line}) does not match to {nfields}")
        return fields



def slurm_datetime(s):
    from datetime import datetime
    d = datetime.strptime(s, '%Y-%m-%dT%H:%M:%S')
    return d


class SlurmDuration(datetime.timedelta):
    def __new__(cls, days=0, seconds=0, microseconds=0, milliseconds=0, minutes=0, hours=0, weeks=0, partition_limit=False):
        self = datetime.timedelta.__new__(cls, days=days,  hours=hours, minutes=minutes, seconds=seconds, microseconds=microseconds)
        self.partition_limit = partition_limit
        return self

    def __repr__(self):
        if self.partition_limit:
            s = 'SlurmDuration(partition_limit=True)'
        else:
            return super().__repr__()

    def __str__(self):
        if self.partition_limit:
            s = 'Partition_Limit'
        else:
            return super().__str__()

    @staticmethod
    def from_string(s):
        """"
        %ld-%2.2ld:%2.2ld:%2.2ld % {days, hours, minutes, seconds}
        "%2.2ld:%2.2ld:%2.2ld" % {days, hours, minutes, seconds}
        """
        import re

        if s == 'Partition_Limit':
            return SlurmDuration(partition_limit=True)

        m = re.match(r'([0-9]+)-([0-9]{2}):([0-9]{2}):([0-9]{2})', s)
        if m:
            days = int(m.group(1))
            hours = int(m.group(2))
            minutes = int(m.group(3))
            seconds = int(m.group(4))
            return SlurmDuration(days=days, hours=hours, minutes=minutes, seconds=seconds)

        m = re.match(r'([0-9]{2}):([0-9]{2}):([0-9]{2})', s)
        if m:
            hours = int(m.group(1))
            minutes = int(m.group(2))
            seconds = int(m.group(3))
            return SlurmDuration(hours=hours, minutes=minutes, seconds=seconds)
        raise ValueError(f"cannot convert {s}, which should be slurm duration, to timedelta")


class SlurmMemory:
    UNITS = "\0KMGTP?"
    PER_CORE_SYMBOL = {None:"", True:'c', False:'n'}

    def __init__(self, size=0, units="M", per_core=False, partition_limit=False, org=None, divisor=1024):
        self.size = size
        self.units = units
        self.per_core = per_core
        self.divisor = divisor
        self.partition_limit = partition_limit
        self.org = org

    def __str__(self):
        if self.partition_limit:
            s = 'Partition_Limit'
        else:
            if isinstance(self.size, float):
                s = f"{self.size:.2f}{self.units}{SlurmMemory.PER_CORE_SYMBOL[self.per_core]}"
            else:
                s = f"{self.size:d}{self.units}{SlurmMemory.PER_CORE_SYMBOL[self.per_core]}"

        if self.org is not None and s != self.org:
            s += f"({self.org})"
        return s

    def __eq__(self, other):
        comparison = ((self.size != other.size) +
                      (self.units != other.units) +
                      (self.per_core != other.per_core) +
                      (self.divisor != other.divisor) +
                      (self.partition_limit != other.partition_limit))
        return comparison == 0
        #self.org = other.org


    @staticmethod
    def from_string(s, divisor=1024):
        import re
        if s == 'Partition_Limit':
            slurm_memory = SlurmMemory(partition_limit=True, org=s, divisor=divisor)
        m = re.match(r"([0-9.]+)([KMGTP?])([cn]?)", s)
        if m is None:
            raise ValueError(f"can not match slurm memory from {s}")

        size = float(m.group(1))
        if float(int(size)) == float(size):
            size = int(size)
        else:
            size = float(size)

        units = m.group(2)
        if units not in SlurmMemory.UNITS:
            raise ValueError(f"Unknown memory units: {units} in {s}")
        per_core_symbol = m.group(3)
        if per_core_symbol == "n":
            per_core = False
        elif per_core_symbol == "c":
            per_core = True
        elif per_core_symbol == "":
            per_core = None
        else:
            raise ValueError(f"Unknown per_core symbol: {per_core_symbol} in {s}")

        slurm_memory = SlurmMemory(size=size, units=units, per_core=per_core, org=s, divisor=divisor)

        if s != '30000M':
            pass
        return slurm_memory

# timedelta(days=1, hours=0, minutes=6)
#
# days: float = ...,
#         seconds: float = ...,
#         microseconds: float = ...,
#         milliseconds: float = ...,
#         minutes: float = ...,
#         hours: float = ...,
#         weeks
