import os
import shlex
import re
from slurmsim import log


def get_sbatch_parser():
    import argparse
    parser = argparse.ArgumentParser("sbatch parser")
    #-dt 871 -e submit_batch_job | -sim-walltime 0
    # -J jobid_1011 --uid=user4 -t 00:30:00 -n 1 --ntasks-per-node=1
    # -A account2 -p normal -q normal
    # --gres=gpu:1  --mem=500000 --constraint=CPU-N pseudo.job
    parser.add_argument('-J','--job-name')
    parser.add_argument('--uid')
    parser.add_argument('-t', '--time')
    parser.add_argument('-n', '--ntasks', type=int)
    parser.add_argument('--ntasks-per-node', type=int)
    parser.add_argument('-A', '--account')
    parser.add_argument('-p', '--partition')
    parser.add_argument('-q', '--qos')
    parser.add_argument('--gres')
    parser.add_argument('--mem')
    # real memory required per node [K|M|G|T]  Default units are megabytes.
    parser.add_argument('-C', '--constraint')
    parser.add_argument('-d', '--dependency')
    # simulated option
    parser.add_argument('-sim-walltime', type=float)
    parser.add_argument('-cancel-in', type=float)
    parser.add_argument('-j','--job-id', type=int)

    parser.add_argument('script')
    return parser


sbatch_parser = get_sbatch_parser()

def mem_to_mb(s):
    """slurm is default in mb unless specified to use gb"""
    if s[-1].upper() == 'K':
        return (int(s[:-1]) + 1023) // 1024
    elif s[-1].upper() == 'M':
        return int(s[:-1])
    elif s[-1].upper() == 'G':
        return int(float(s[:-1]) * 1024)
    elif s[-1].upper() == 'T':
        return int(float(s[:-1]) * 1024 * 1024)
    else:
        return int(s)

def parse_sbatch_args(args):
    args = sbatch_parser.parse_args(args=args)

    # job id
    if args.job_id is None and args.job_name is not None:
        m = re.match("jobid_(\d+)", args.job_name)
        if not m:
            m = re.match("job_(\d+)", args.job_name)
        if m:
            args.job_id = int(m.group(1))

    return args


class SimEvent:
    """
    Generalized Job
    """
    def __init__(self):
        # contains event type and activation time
        self.activate_time = None
        self.event_type = None
        # contains event details
        self.payload = {}

    def read_from_eventline(self, line):
        sleep_job = "sleep.job"

        line = line.strip()
        if len(line) == 0:
            # skip empty line
            return None
        if line[0] == "#":
            # skip comment
            return None

        event_command, event_details = line.split("|")
        event_command = event_command.strip().split()
        event_details = event_details.strip()

        dt = float(event_command[event_command.index("-dt") + 1])
        etype = event_command[event_command.index("-e") + 1]

        self.activate_time = dt
        self.event_type = etype

        if etype == "submit_batch_job":
            self.payload = parse_sbatch_args(shlex.split(event_details))

    def __str__(self):
        return f"{self.activate_time} {self.event_type} {str(self.payload)}"

    @classmethod
    def from_eventline(cls, line):
        event = cls()
        event.read_from_eventline(line)
        return event


class SimEventList:
    def __init__(self):
        self.event = []

    def __str__(self):
        s = ""
        for e in self.event:
            s += str(e) + "\n"
        return s

    def read_events_file(self, events_file_name):
        self.event = []

        with open(events_file_name, "rt") as fin:
            for m_line in fin:
                event = SimEvent.from_eventline(m_line)
                if event:
                    self.event.append(event)
                    #self.event.append({"dt":dt,"etype":etype,"payload":payload})
        log.info(f"Read from {events_file_name} {len(self.event)} events")

    def write_bsc_swf(self, filename):
        import math
        from slurmanalyser.utils import util_slurm_duration_to_timedelta
        dummy=-1
        last_job_id = 0
        with open(filename, "wt") as fout:
            for e in self.event:
                if e.event_type == "submit_batch_job":
                    wclimit_seconds = util_slurm_duration_to_timedelta(e.payload.time).total_seconds()
                    print(wclimit_seconds, math.ceil(wclimit_seconds/60.0), e.payload.time)
                    if e.payload.job_id is not None:
                        job_id = e.payload.job_id
                    else:
                        job_id = last_job_id + 1
                    last_job_id = job_id

                    if e.payload.gres is not None:
                        log.error("bsc swf format don't support gres! job: " + str(e.payload.job_name))
                    if e.payload.constraint is not None:
                        log.error("bsc swf format don't support constraint! job: " + str(e.payload.job_name))
                    if e.payload.cancel_in is not None:
                        log.error("bsc swf format don't support cancel_in! job: " + str(e.payload.job_name))
                    if e.payload.dependency is not None:
                        log.warning("bsc swf format don't support dependency! was not tested! job: " + str(e.payload.job_name))
                    # 3;3;-1;950;8;-1;-1;-1;-1;-1;1;tester;-1;-1;1;esb;-1;-1;esb,dam,cm
                    s = "%d;%ld;%d;%d;%d;%ld;%d;%ld;%d;%ld;%d;%s;%s;%ld;%s;%s;%s;%ld;%s\n" % (
                        job_id,  # %d;
                        round(e.activate_time),  # %ld;
                        dummy,  # e.payload.wait_modular_job_time,  # %d;
                        round(e.payload.sim_walltime),  # %d;
                        e.payload.ntasks,  # %d;
                        dummy,  # %ld;
                        mem_to_mb(e.payload.mem) if e.payload.mem is not None else -1,  # rreq_memory_per_node %d;
                        dummy,  # %ld;
                        math.ceil(wclimit_seconds),  # %d; wallclack limit in seconds (will be converted to minutes internally)
                        dummy,  # %ld;
                        dummy,  # status, %d;
                        e.payload.uid,  # %s;
                        e.payload.account,  # %s;
                        dummy,  # %ld;
                        e.payload.qos,  # %s;
                        e.payload.partition,  # %s;
                        e.payload.dependency if e.payload.dependency is not None else "",  # %s;
                        dummy,  # %ld;
                        ""  # module_list # %s
                    )
                    fout.write(s)


def convert_workload(ievents=None, oswf=None):
    events_list = SimEventList()
    events_list.read_events_file(ievents)
    events_list.write_bsc_swf(oswf)
    # print(ievents,oswf)
    # print(events_list)

