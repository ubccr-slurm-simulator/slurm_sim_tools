#!/usr/bin/env python3
import os
import sys
import re
from collections import OrderedDict
from collections import deque
import pprint
import logging as log
import datetime
import pandas as pd
import traceback
import tqdm
import multiprocessing
from slurmsim.log import verbose

def process_squeue_output(cluster,filename=None,lines=None):
    if filename!=None and lines==None:
        with open(filename,"rt") as fin:
            lines=fin.readlines()
    if filename==None:
        filename="None"
        
    if lines==None:
        raise Exception(filename+" can not be read or incorrect format")
    if len(lines)==0:
        raise Exception(filename+" can not be read or incorrect format")
    if len(lines)<10:
        raise Exception(filename+" can not be read or incorrect format")
    
    r=OrderedDict()
    
    #roll to proper cluster
    i=0
    N=len(lines)
    while i<N:
        if lines[i].count('CLUSTER:') and lines[i].count(cluster):
            break
        i+=1
    if i==N:
        raise Exception("Clueste "+cluster+" is not present in squeue output")
    if not (lines[i].count('CLUSTER:') and lines[i].count(cluster)):
        raise Exception("Clueste "+cluster+" is not present in squeue output")
    
    #read header
    i+=1
    Header=lines[i].strip().split()[:5]
    iHeader={}
    for j,h in zip(range(len(Header)),Header):
        r[h]=[]
        iHeader[h]=j
    i+=1
    while i<N:
        l=lines[i].strip().replace(', ',',')
        if len(l)<45:break
        
        fields=[]
        #split fields
        fixed=(0,8,18,27,36,45)
        for j in range(len(fixed)-1):
            fields.append(l[fixed[j]:fixed[j+1]])
        
        #fields+=l[fixed[-1]:].split()
        
                  
        if len(fields)==0: break
        if fields[0]=="CLUSTER:": break
        
        
        if len(fields)!=len(Header):
            print(len(fields),len(Header))
            log.error("squeue incorect number of fields."+filename+" "+l)
            exit()
            i+=1
            continue
        
        for j,v in zip(range(len(fields)),fields):
            r[Header[j]].append(v)
        
        i+=1
    
    state=pd.Series(r['STATE'])
    
    return state.value_counts()




def get_datatime(line):
    try:
        i = line.index("]")
    except ValueError:
        return None,None
    if len(line)<25:
        return None,None

    m_t = datetime.datetime.strptime(line[:(i+1)],"[%Y-%m-%dT%H:%M:%S.%f]")
    m_ts = m_t.strftime("%Y-%m-%d %H:%M:%S.%f")
    return m_t, m_ts


def process_slurmctrd_logs(log_filename,csv_filename, top_dir, num_of_proc=1, time="time", job_id="job_id"):
    """

    @param log_filename:
    @param csv_filename:
    @param top_dir:
    @param num_of_proc:
    @param time: time - use datatime, first_job - time in sec from first job submission
    @return:
    """
    kwargs = {'time': time,'job_id':job_id}
    if top_dir is None:
        return m_process_slurmctrd_log([log_filename, csv_filename, kwargs])
    else:
        log.info(f"Looking in {top_dir} for {log_filename}")
        args_to_process = []
        for root, dirs, files in os.walk(top_dir):
            for file in files:
                if file == log_filename:
                    args_to_process.append([os.path.join(root, file), os.path.join(root, csv_filename), kwargs])

        log.info(f"Found {len(args_to_process)} files to process")



        if num_of_proc == 1:
            for args in args_to_process:
                m_process_slurmctrd_log(args)
        else:
            pool = multiprocessing.Pool(processes=num_of_proc)
            for _ in tqdm.tqdm(pool.imap_unordered(m_process_slurmctrd_log, args_to_process), total=len(args_to_process)):
                pass


def m_process_slurmctrd_log(a):
    return ProcessSlurmCtrdLog(a[0],a[1],**a[2]).run()


class ProcessSlurmCtrdLog:
    def __init__(self, log_filename, csv_filename, time='time', job_id="job_id"):
        self.log_filename = log_filename
        self.csv_filename = csv_filename
        self.time = time # can be first_job, time or datetime
        self.job_id_method = job_id
        self.records = {'datetime': [], 'ts': [], 'job_id': [], 'metric': [], 't': [], 'value': []}
        self.job_name_to_id = {}
        self.job_id_to_name = {}
        self.job_id_to_ref_id = {}

        self.process_create_real_time = None
        self.process_create_sim_time = None

    def init_records(self, filename):
        self.records = {'datetime': [], 'ts': [], 'job_id': [], 'metric': [], 't': [], 'value': []}

    def add_record(self, job_id, metric, t, value):
        self.records['datetime'].append(t)
        self.records['ts'].append(t)
        self.records['t'].append(t)
        self.records['job_id'].append(job_id)
        self.records['metric'].append(metric)
        self.records['value'].append(str(value))

    def finalize_records(self):
        if self.time == "first_job":
            ref_time = None
            for i in range(len(self.records['ts'])):
                if self.records['metric'][i] == "submit_job":
                    ref_time = self.records['t'][i]
                    break
            if ref_time is None:
                log.error("Can not find submit time for first job! Rollback to use time.")
                self.time == "time"
            else:
                log.debug("Submit time for first job: %s", ref_time.strftime("%Y-%m-%d %H:%M:%S.%f"))
                for i in range(len(self.records['ts'])):
                    self.records['t'][i] = f"{(self.records['t'][i]-ref_time).total_seconds():.6f}"
        for i in range(len(self.records['ts'])):
            self.records['ts'][i] = self.records['ts'][i].strftime("%Y-%m-%d %H:%M:%S.%f")

        if self.time == "since_process_created":
            log.debug("Submit time for first job: %s", self.process_create_sim_time.strftime("%Y-%m-%d %H:%M:%S.%f"))
            ref_time = self.process_create_sim_time
            for i in range(len(self.records['ts'])):
                self.records['t'][i] = f"{(self.records['t'][i] - ref_time).total_seconds():.6f}"

        if self.job_id_method == "job_name":
            if len(self.job_id_to_name) == 0:
                log.errog("No job names will use ids!")
                self.job_id_method == "job_id"
            else:
                self.records['job_name'] = [v for v in self.records['job_id']]
                for i in range(len(self.records['ts'])):
                    if self.records['job_id'][i] != "NA":
                        if self.records['job_name'][i] in self.job_id_to_name:
                            self.records['job_name'][i] = self.job_id_to_name[self.records['job_id'][i]]
                        else:
                            log.error("job id %s has no name", self.records['job_id'][i])

        if self.job_id_method == "job_rec_id":
            if len(self.job_id_to_ref_id)==0:
                log.error("No job names will use ids!")
                self.job_id_method == "job_id"
            else:
                self.records['job_rec_id'] = [v for v in self.records['job_id']]
                for i in range(len(self.records['ts'])):
                    if self.records['job_rec_id'][i] != "NA":
                        if self.records['job_rec_id'][i] in self.job_id_to_ref_id:
                            self.records['job_rec_id'][i] = self.job_id_to_ref_id[self.records['job_id'][i]]
                        else:
                            log.error("job id %s has no ref_id", self.records['job_id'][i])

    def write_records(self):
        if self.csv_filename is None:
            return
        import slurmanalyser.utils
        file_records_out = slurmanalyser.utils.get_file_open(self.csv_filename)(self.csv_filename, "wt")
        import csv
        writer = csv.writer(file_records_out)

        if verbose:
            print("%-28s %-12s %-32s %-28s %-32s" % ("ts", self.job_id_method, 'metric', 't', 'value'))

        writer.writerow(["ts",self.job_id_method, 'metric', 't', 'value'])

        for i in range(len(self.records['ts'])):
            record = [self.records['ts'][i], self.records[self.job_id_method][i],
                      self.records['metric'][i], self.records['t'][i], self.records['value'][i]]
            if verbose:
                print("%-12s %-32s %-28s %-32s" % tuple(record))
            writer.writerow(record)

        file_records_out.close()
        file_records_out = None

    def get_sim_start_datetime(self):
        import slurmanalyser.utils
        fin = slurmanalyser.utils.get_file_open(self.log_filename)(self.log_filename, "rt")
        first_line = fin.readline()
        m_t, m_ts = get_datatime(first_line)
        print("first_line",first_line,m_t,m_ts)
        return m_t

    def get_sim_end_datetime(self):
        import slurmanalyser.utils
        import os

        fin = slurmanalyser.utils.get_file_open(self.log_filename)(self.log_filename, "rb")
        try:  # catch OSError in case of a one line file
            fin.seek(-2, os.SEEK_END)
            while fin.read(1) != b'\n':
                fin.seek(-2, os.SEEK_CUR)
        except OSError:
            fin.seek(0)
        last_line = fin.readline().decode()
        m_t, m_ts = get_datatime(last_line)
        print("last_line",last_line,m_t,m_ts)
        return m_t

    def run(self):
        import slurmanalyser.utils
        r=[]
        if not os.path.isfile(self.log_filename):
            raise Exception("File %s do not exits" % self.log_filename)

        fin = slurmanalyser.utils.get_file_open(self.log_filename)(self.log_filename, "rt")
        self.init_records(self.csv_filename)

        window_size = 600
        window = deque(maxlen=window_size)

        #logs_first_message=


        # initial window fill
        for i in range(window_size):
            window.append(fin.readline().rstrip('\n'))

        m_t, m_ts = get_datatime(window[0])
        if m_t:
            self.add_record("NA", "slurm_start_time", m_t, "NA")

        line_number = 1
        eof_count = 0
        while True:

            m = re.search("Processing RPC: REQUEST_SUBMIT_BATCH_JOB from (?:uid|UID)=(\S*)", window[0])
            if m:
                m_t, m_ts = get_datatime(window[0])
                m_uid = m.group(1)
                m_job_name = None
                m_job_id = None
                m_job_rec_id = None
                m_priority = None
                for i in range(1,window_size):
                    if m_job_name is None and re.search("JobDesc: user_id=", window[i]):
                        m = re.search("JobDesc: user_id=\S* JobId=\S* partition=\S* name=(\S*)", window[i])
                        m_job_name = m.group(1)

                    if m_job_id is None and re.search("initial priority for job \S* is ", window[i]):
                        m = re.search("initial priority for job (\S+) is (\d+)", window[i])
                        m_job_id = m.group(1)
                        m_priority = m.group(2)
                    if m_job_name is not None and m_job_id is not None:
                        break

                if m_job_name is not None:
                    m = re.match("jobid_(\d+)", m_job_name)
                    if m:
                        m_job_name__m_job_id = m.group(1)
                        m_job_rec_id = str(int(m_job_name__m_job_id))
                        if m_job_id is not None:
                            if m_job_id != m_job_rec_id:
                                print("Error: job id dont match %s != %s" % (
                                m_job_id, m_job_rec_id))
                        else:
                            print("Error: didn't find job id, set it from job name (%s). Please check the match by other means" % (m_job_name__m_job_id))
                            m_job_id = m_job_name__m_job_id
                    else:
                        print(
                            "Warning: job name (%s) is not in jobid_<job id> format" % m_job_name)

                if m_job_name is not None and m_job_id is not None:
                    self.add_record(m_job_id, "job_name", m_t, m_job_name)
                    self.add_record(m_job_id, "uid", m_t, m_uid)
                    self.add_record(m_job_id, "submit_job", m_t,"NA")

                    self.job_name_to_id[m_job_name] = m_job_id
                    self.job_id_to_name[m_job_id] = m_job_name
                    if m_job_rec_id:
                        self.job_id_to_ref_id[m_job_id] = m_job_rec_id
                else:
                    print("Error: something is wrong can identify job_name or m_job_id on line %d" % line_number)
                if m_priority:
                    self.add_record(m_job_id, "initial_priority", m_t, m_priority)

            m = re.search("sched: Allocate JobId=(\S+) NodeList=(\S+)", window[0])
            if m:
                m_t, m_ts = get_datatime(window[0])
                m_job_id = m.group(1)
                m_nodes = m.group(2)
                self.add_record(m_job_id, "launch_job", m_t, "sched")
                self.add_record(m_job_id, "nodes", m_t, m_nodes)

            #[2022-02-02T13:51:06.147191] sched/backfill: _start_job: Started JobId=1001 in normal on n1
            m = re.search("backfill: Started JobId=(\S+) in \S+ on (\S+)", window[0])
            if m:
                m_t, m_ts = get_datatime(window[0])
                m_job_id = m.group(1)
                m_nodes = m.group(2)
                self.add_record(m_job_id, "launch_job", m_t, "backfill")
                self.add_record(m_job_id, "nodes", m_t, m_nodes)
            # [2022-02-02T13:51:06.147191] sched/backfill: _start_job: Started JobId=1001 in normal on n1
            m = re.search("sched/backfill: _start_job: Started JobId=(\S+) in \S+ on (\S+)", window[0])
            if m:
                m_t, m_ts = get_datatime(window[0])
                m_job_id = m.group(1)
                m_nodes = m.group(2)
                self.add_record(m_job_id, "launch_job", m_t, "backfill")
                self.add_record(m_job_id, "nodes", m_t, m_nodes)

            m = re.search("Processing RPC: REQUEST_COMPLETE_BATCH_SCRIPT from uid=\S+ JobId=(\d+)", window[0])
            if m:
                m_t, m_ts = get_datatime(window[0])
                m_job_id = m.group(1)
                self.add_record(m_job_id, "request_complete_job", m_t,"NA")
            m = re.search("_slurm_rpc_complete_batch_script JobId=(\d+)", window[0])
            if m:
                m_t, m_ts = get_datatime(window[0])
                m_job_id = m.group(1)
                self.add_record(m_job_id, "request_complete_job", m_t,"NA")
            # [2022-01-27T18:01:51.406889] _job_complete: JobId=1000 WEXITSTATUS 0
            # [2022-01-27T18:01:51.406948] accounting_storage/slurmdbd: _agent: agent_count:1
            # [2022-01-27T18:01:51.407044] debug3: select/cons_res: job_res_rm_job: JobId=1000 action:normal
            # [2022-01-27T18:01:51.407052] debug3: select/cons_res: job_res_rm_job: removed JobId=1000 from part normal row 0
            # [2022-01-27T18:01:51.407064] AGENT: agent_trigger: pending_wait_time=65534->999 mail_too=F->F Agent_cnt=0 agent_thread_cnt=0 retry_list_size=1
            # [2022-01-27T18:01:51.407073] _job_complete: JobId=1000 done
            # [2022-01-27T18:01:51.407079] debug2: _slurm_rpc_complete_batch_script JobId=1000 usec=270


            m = re.search("Spawning RPC agent for msg_type REQUEST_TERMINATE_JOB for JobId=(\S+)", window[0])
            if m:
                m_t, m_ts = get_datatime(window[0])
                m_job_id = m.group(1)
                self.add_record(m_job_id, "request_terminate_job", m_t,"NA")

            m = re.search("Time limit exhausted for JobId=(\S+)", window[0])
            if m:
                m_t, m_ts = get_datatime(window[0])
                m_job_id = m.group(1)
                self.add_record(m_job_id, "time_limit_exhausted", m_t, "NA")

            m = re.search("Spawning RPC agent for msg_type REQUEST_KILL_TIMELIMIT for JobId=(\S+)", window[0])
            if m:
                m_t, m_ts = get_datatime(window[0])
                m_job_id = m.group(1)
                self.add_record(m_job_id, "request_kill_timelimit", m_t, "NA")

            m = re.search("Processing RPC: MESSAGE_EPILOG_COMPLETE uid=\S+ JobId=(\S+)", window[0])
            if m:
                m_t, m_ts = get_datatime(window[0])
                m_job_id = m.group(1)
                self.add_record(m_job_id, "message_epilog_complete", m_t, "NA")

            m = re.search("job_epilog_complete for JobId=(\S+) with node=(\S+)", window[0])
            if m:
                m_t, m_ts = get_datatime(window[0])
                m_job_id = m.group(1)
                m_node = m.group(2)
                self.add_record(m_job_id, "job_epilog_complete", m_t, m_node)

            # slurm controller events
            if re.search("backfill: beginning", window[0]):
                m_t, m_ts = get_datatime(window[0])
                self.add_record("NA", "backfill", m_t,"start")
            if re.search("backfill: reached end of job queue", window[0]):
                m_t, m_ts = get_datatime(window[0])
                self.add_record("NA", "backfill", m_t, "end")
            m = re.search("backfill: completed testing ([0-9]+)\(([0-9]+)\) jobs, usec=([0-9.]+)", window[0])
            if m:
                m_t, m_ts = get_datatime(window[0])
                self.add_record("NA", "backfill_cycle_n", m_t, m.group(2))
                self.add_record("NA", "backfill_cycle_time", m_t, float(m.group(3))*1e6)
            # backfill: completed testing 2(2) jobs, usec=1773

            if re.search("sched: Running job scheduler", window[0]):
                m_t, m_ts = get_datatime(window[0])
                self.add_record("NA", "sched", m_t,"start")

            if re.search("Testing job time limits and checkpoints", window[0]):
                m_t, m_ts = get_datatime(window[0])
                self.add_record("NA", "job_time_limits_testing", m_t,"NA")

            if re.search("_slurmctld_background pid = ", window[0]):
                m_t, m_ts = get_datatime(window[0])
                self.add_record("NA", "slurmctld_background", m_t,"NA")

            # sim events
            # m = re.search("sim: process create real utime: ([0-9]+), process create sim utime: ([0-9]+)", window[0])
            # if m:
            #     m_t, m_ts = get_datatime(window[0])
            #     process_create_real_time = int(m.group(1))/1000000.0
            #     process_create_sim_time = int(m.group(2))/1000000.0
            #     add_record("NA", "process_create_real_time", m_t, "%.6f" % process_create_real_time)
            #     add_record("NA", "process_create_sim_time", m_t, "%.6f" % process_create_sim_time)

            m = re.search(
                "sim: process create real time: (\S+), process create sim time: (\S+)",
                window[0])
            if m:
                m_t, m_ts = get_datatime(window[0])
                process_create_real_time = m.group(1)
                process_create_sim_time = m.group(2)
                self.add_record("NA", "process_create_real_time", m_t,
                           process_create_real_time)
                self.add_record("NA", "process_create_sim_time", m_t,
                           process_create_sim_time)
                self.process_create_real_time = datetime.datetime.strptime(process_create_real_time, "%Y-%m-%dT%H:%M:%S.%f")
                self.process_create_sim_time = datetime.datetime.strptime(process_create_sim_time, "%Y-%m-%dT%H:%M:%S.%f")

            # debug3("Calling schedule from epilog_complete");
            # debug3("Calling queue_job_scheduler from epilog_complete");
            m = re.search(
                r"Calling (schedule|queue_job_scheduler) from (\S+)",
                window[0])
            if m:
                m_t, m_ts = get_datatime(window[0])
                self.add_record("NA", "calling_" + m.group(1), m_t, m.group(2))

            # debug3("Calling schedule from _slurmctld_background %ld %ld %ld",now,last_sched_time,now-last_sched_time);
            m = re.search(
                r"Calling schedule from _slurmctld_background (\S+) (\S+) (\S+)",
                window[0])
            if m:
                m_t, m_ts = get_datatime(window[0])
                self.add_record("NA", "_slurmctld_background_call_sched", m_t, m.group(1))

            # debug3("_slurmctld_background cycle");
            m = re.search(
                r"_slurmctld_background cycle",
                window[0])
            if m:
                m_t, m_ts = get_datatime(window[0])
                self.add_record("NA", "_slurmctld_background_cycle", m_t, "NA")

            # read next line
            line = fin.readline()
            window.append(line.rstrip('\n'))
            line_number += 1
            if not line:
                eof_count += 1
            if eof_count >= window_size:
                break

        self.finalize_records()
        fin.close()
        self.write_records()


if __name__ == '__main__':
    
    import argparse
        
    parser = argparse.ArgumentParser(description='process sdiag')
    
    parser.add_argument('-l', '--log', required=True, type=str,
        help="slurmctrd log")
    parser.add_argument('-csv', '--csv', default="squeue.csv", type=str,
        help="name of output csv file")
    parser.add_argument('-v', '--verbose', action='store_true', 
        help="turn on verbose logging")
    
    args = parser.parse_args()
    if args.verbose:
        log.basicConfig(level=log.DEBUG,format='[%(asctime)s]-[%(levelname)s]: %(message)s')
    else:
        log.basicConfig(level=log.INFO,format='[%(asctime)s]-[%(levelname)s]: %(message)s')

    verbose = args.verbose
    process_slurmctrd_log(args.log,args.csv)
    