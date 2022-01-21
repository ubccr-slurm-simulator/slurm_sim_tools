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

verbose = False

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


file_records_out = None


def init_records(filename):
    global file_records_out
    import slurmanalyser.utils
    file_records_out = slurmanalyser.utils.get_file_open(filename)(filename, "wt")
    file_records_out.write("job_id,metric,t,value\n")


def add_record(job_id, metric, t, value):
    global file_records_out
    record = (job_id, metric, t, str(value))
    global verbose
    if verbose:
        print("%-6s %-32s %-28s %-32s" % record)
    file_records_out.write(",".join(record)+"\n")


def finalize_records():
    global file_records_out
    file_records_out.close()
    file_records_out = None


def process_slurmctrd_logs(log_filename,csv_filename, top_dir, num_of_proc=1):
    if top_dir is None:
        return process_slurmctrd_log(log_filename,csv_filename)
    else:
        log.info(f"Looking in {top_dir} for {log_filename}")
        args_to_process = []
        for root, dirs, files in os.walk(top_dir):
            for file in files:
                if file == log_filename:
                    args_to_process.append([os.path.join(root, file), os.path.join(root, csv_filename)])

        log.info(f"Found {len(args_to_process)} files to process")



        if num_of_proc == 1:
            for args in args_to_process:
                m_process_slurmctrd_log(args)
        else:
            pool = multiprocessing.Pool(processes=num_of_proc)
            for _ in tqdm.tqdm(pool.imap_unordered(m_process_slurmctrd_log, args_to_process), total=len(args_to_process)):
                pass

def m_process_slurmctrd_log(a):
    return process_slurmctrd_log(a[0],a[1])

def process_slurmctrd_log(log_filename,csv_filename):
    import slurmanalyser.utils
    r=[]
    if not os.path.isfile(log_filename):
        raise Exception("File %s do not exits" % log_filename)

    fin = slurmanalyser.utils.get_file_open(log_filename)(log_filename, "rt")
    init_records(csv_filename)

    window_size = 200
    window = deque(maxlen=window_size)

    #logs_first_message=


    # initial window fill
    for i in range(window_size):
        window.append(fin.readline().rstrip('\n'))

    m_t, m_ts = get_datatime(window[0])
    if m_ts:
        add_record("NA", "slurm_start_time", m_ts, "NA")

    line_number = 1
    eof_count = 0
    while True:

        m = re.search("Processing RPC: REQUEST_SUBMIT_BATCH_JOB from uid=(\S*)", window[0])
        if m:
            m_t, m_ts = get_datatime(window[0])
            m_uid = m.group(1)
            m_job_name = None
            m_job_id = None
            for i in range(1,window_size):
                if m_job_name is None and re.search("JobDesc: user_id=", window[i]):
                    m = re.search("JobDesc: user_id=\S* JobId=\S* partition=\S* name=(\S*)", window[i])
                    m_job_name = m.group(1)

                if m_job_id is None and re.search("debug2: initial priority for job \S* is ", window[i]):
                    m = re.search("debug2: initial priority for job (\S*) is ", window[i])
                    m_job_id = m.group(1)
                if m_job_name is not None and m_job_id is not None:
                    break

            if m_job_name is not None:
                m = re.match("jobid_(\S+)", m_job_name)
                if m:
                    m_job_name__m_job_id = m.group(1)
                    if m_job_id is not None:
                        if m_job_id != m.group(1):
                            print("Error: job id dont match %s != %s" % (
                            m_job_id, m.group(1)))
                    else:
                        print("Error: didn't find job id, set it from job name (%s). Please check the match by other means" % (m_job_name__m_job_id))
                        m_job_id = m_job_name__m_job_id
                else:
                    print(
                        "Warning: job name (%s) is not in jobid_<job id> format" % m_job_name)

            if m_job_name is not None and m_job_id is not None:
                add_record(m_job_id, "job_name", m_ts, m_job_name)
                add_record(m_job_id, "uid", m_ts, m_uid)
                add_record(m_job_id, "submit_job", m_ts,"NA")
            else:
                print("Error: something is wrong can identify job_name or m_job_id on line %d" % line_number)

        m = re.search("sched: Allocate JobId=(\S+) NodeList=(\S+)", window[0])
        if m:
            m_t, m_ts = get_datatime(window[0])
            m_job_id = m.group(1)
            m_nodes = m.group(2)
            add_record(m_job_id, "launch_job", m_ts, "sched")
            add_record(m_job_id, "nodes", m_ts, m_nodes)

        m = re.search("backfill: Started JobId=(\S+) in \S+ on (\S+)", window[0])
        if m:
            m_t, m_ts = get_datatime(window[0])
            m_job_id = m.group(1)
            m_nodes = m.group(2)
            add_record(m_job_id, "launch_job", m_ts, "backfill")
            add_record(m_job_id, "nodes", m_ts, m_nodes)

        m = re.search("Processing RPC: REQUEST_COMPLETE_BATCH_SCRIPT from uid=\S+ JobId=(\S+)", window[0])
        if m:
            m_t, m_ts = get_datatime(window[0])
            m_job_id = m.group(1)
            add_record(m_job_id, "request_complete_job", m_ts,"NA")

        m = re.search("Spawning RPC agent for msg_type REQUEST_TERMINATE_JOB for JobId=(\S+)", window[0])
        if m:
            m_t, m_ts = get_datatime(window[0])
            m_job_id = m.group(1)
            add_record(m_job_id, "request_terminate_job", m_ts,"NA")

        m = re.search("Time limit exhausted for JobId=(\S+)", window[0])
        if m:
            m_t, m_ts = get_datatime(window[0])
            m_job_id = m.group(1)
            add_record(m_job_id, "time_limit_exhausted", m_ts, "NA")

        m = re.search("Spawning RPC agent for msg_type REQUEST_KILL_TIMELIMIT for JobId=(\S+)", window[0])
        if m:
            m_t, m_ts = get_datatime(window[0])
            m_job_id = m.group(1)
            add_record(m_job_id, "request_kill_timelimit", m_ts, "NA")

        m = re.search("Processing RPC: MESSAGE_EPILOG_COMPLETE uid=\S+ JobId=(\S+)", window[0])
        if m:
            m_t, m_ts = get_datatime(window[0])
            m_job_id = m.group(1)
            add_record(m_job_id, "message_epilog_complete", m_ts, "NA")

        m = re.search("job_epilog_complete for JobId=(\S+) with node=(\S+)", window[0])
        if m:
            m_t, m_ts = get_datatime(window[0])
            m_job_id = m.group(1)
            m_node = m.group(2)
            add_record(m_job_id, "job_epilog_complete", m_ts, m_node)

        # slurm controller events
        if re.search("backfill: beginning", window[0]):
            m_t, m_ts = get_datatime(window[0])
            add_record("NA", "backfill", m_ts,"start")
        if re.search("backfill: reached end of job queue", window[0]):
            m_t, m_ts = get_datatime(window[0])
            add_record("NA", "backfill", m_ts, "end")
        m = re.search("backfill: completed testing ([0-9]+)\(([0-9]+)\) jobs, usec=([0-9.]+)", window[0])
        if m:
            m_t, m_ts = get_datatime(window[0])
            add_record("NA", "backfill_cycle_n", m_ts, m.group(2))
            add_record("NA", "backfill_cycle_time", m_ts, float(m.group(3))*1e6)
        # backfill: completed testing 2(2) jobs, usec=1773

        if re.search("sched: Running job scheduler", window[0]):
            m_t, m_ts = get_datatime(window[0])
            add_record("NA", "sched", m_ts,"start")

        if re.search("Testing job time limits and checkpoints", window[0]):
            m_t, m_ts = get_datatime(window[0])
            add_record("NA", "job_time_limits_testing", m_ts,"NA")

        # sim events
        # m = re.search("sim: process create real utime: ([0-9]+), process create sim utime: ([0-9]+)", window[0])
        # if m:
        #     m_t, m_ts = get_datatime(window[0])
        #     process_create_real_time = int(m.group(1))/1000000.0
        #     process_create_sim_time = int(m.group(2))/1000000.0
        #     add_record("NA", "process_create_real_time", m_ts, "%.6f" % process_create_real_time)
        #     add_record("NA", "process_create_sim_time", m_ts, "%.6f" % process_create_sim_time)

        m = re.search(
            "sim: process create real time: (\S+), process create sim time: (\S+)",
            window[0])
        if m:
            m_t, m_ts = get_datatime(window[0])
            process_create_real_time = m.group(1)
            process_create_sim_time = m.group(2)
            add_record("NA", "process_create_real_time", m_ts,
                       process_create_real_time)
            add_record("NA", "process_create_sim_time", m_ts,
                       process_create_sim_time)

        # read next line
        line = fin.readline()
        window.append(line.rstrip('\n'))
        line_number += 1
        if not line:
            eof_count += 1
        if eof_count >= window_size:
            break

    finalize_records()
    fin.close()


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
    