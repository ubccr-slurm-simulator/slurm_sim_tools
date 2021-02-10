#!/usr/bin/env python3
import os
import sys
import subprocess
import logging as log
from pprint import pprint
import shutil
import pymysql
import pwd
import signal
import pandas as pd
import traceback
import inspect
from time import sleep,time
import re
import math
import getpass
import psutil
import json
import datetime
from collections import OrderedDict
from sperf import get_process_realtimestat, system_info

slurmdbd_proc=None
slurmdbd_out=None
slurmctld_proc=None
slurmctld_out=None
slurmd_proc=None
slurmd_out=None
monitor_proc=None
trace=None

def demote(user_uid, user_gid):
    def result():
        report_ids('starting demotion')
        os.setgid(user_gid)
        os.setuid(user_uid)
        report_ids('finished demotion')
    return result


def report_ids(msg):
    log.debug('uid, gid = %d, %d; %s' % (os.getuid(), os.getgid(), msg))

#[slurmdbd_loc,'-Dvv'],env={'SLURM_CONF':slurm_conf_loc},
#                                   stdout=slurmdbd_out,stderr=slurmdbd_out

def run_as_otheruser(username,args,**kwargs):
    cwd=os.getcwd()
    pw_record = pwd.getpwnam(username)
    username      = pw_record.pw_name
    user_home_dir  = pw_record.pw_dir
    user_uid       = pw_record.pw_uid
    user_gid       = pw_record.pw_gid
    env = os.environ.copy()
    env['HOME'     ]  = user_home_dir
    env['LOGNAME'  ]  = username
    env['PWD'      ]  = cwd  if 'cwd' not in kwargs else kwargs['cwd']
    env['USER'     ]  = username
    env['USERNAME' ]  = username
    if 'env' in kwargs:
        env.update(kwargs['env'])
    kwargs['env']=env

    #if username=="root":
    #    args = ['sudo'] + args
    #else:
    kwargs['preexec_fn']=demote(user_uid, user_gid)
    
    if 'cwd' not in kwargs:
        kwargs['cwd']=cwd

    #pprint(args)
    #pprint(kwargs)
    
    process = subprocess.Popen(
        args, **kwargs
    )
    return process

def slurm_conf_parser(slurm_conf_loc):
    """very simple parser to get some parameters from slurm.conf"""
    if not os.path.isfile(slurm_conf_loc):
        raise Exception("Can not find slurm.conf at "+slurm_conf_loc)
    
    params = {
        'SlurmdUser': 'root'
    }
    with open(slurm_conf_loc,'rt') as fin:
        lines=fin.readlines()
        for l in lines:
            l=l.strip()
            if len(l)==0:
                continue
            if l[0]=='#':
                continue
            comment=l.find('#')
            if comment>=0:
                l=l[:comment]
                l=l.strip()
            
            setsign=l.find('=')
            if setsign>=0:
                name=l[:setsign].strip()
                if len(l)>setsign+1:
                    value=l[setsign+1:].strip()
                else:
                    value="None"
                params[name.lower()]=value
            
    return params

def signal_handler(m_signal, frame):
    print('Ctrl+C intercepted, exiting...')
    if slurmdbd_proc!=None:
        slurmdbd_proc.kill()
    if slurmctld_proc!=None:
        slurmctld_proc.kill()
    if slurmd_proc!=None:
        slurmd_proc.kill()
    if monitor_proc!=None:
        monitor_proc.kill()
    
    if slurmctld_out!=None and slurmctld_out!=subprocess.DEVNULL:
        slurmctld_out.close()
    if slurmdbd_out!=None and slurmdbd_out!=subprocess.DEVNULL:
        slurmdbd_out.close()
    if slurmd_out!=None and slurmd_out!=subprocess.DEVNULL:
        slurmd_out.close()
    
    sys.exit(0)

def read_trace_and_prep_scripts_old(trace_file_name):
    global trace
    trace=pd.read_csv(trace_file_name)
    
    sim_submit_ts0=trace.sim_submit_ts.min()
    trace.sim_submit_ts=trace.sim_submit_ts-sim_submit_ts0
    trace['script_path']='/home/'+trace.sim_username+'/slurm_scripts/'+trace.sim_job_id.apply(str)+".sh"
    
    for index, job in trace.iterrows():
        #generate script
        script="#!/bin/bash\n"
        script+="#SBATCH -t %02d:%02d:00\n"%(job.sim_wclimit//60,job.sim_wclimit%60)
        script+="#SBATCH --ntasks=%d\n"%(job.sim_tasks,)
        script+="#SBATCH --ntasks-per-node=%d\n"%(job.sim_tasks_per_node,)
        if not pd.isnull(job.sim_features) and job.sim_features!="":
            script+="#SBATCH -C %s\n"%(job.sim_features,)
        if not pd.isnull(job.sim_req_mem) and not pd.isnull(job.sim_req_mem_per_cpu):
            if job.sim_req_mem_per_cpu:
                script+="#SBATCH --mem-per-cpu=%d\n"%(job.sim_req_mem,)
            else:
                script+="#SBATCH --mem=%d\n"%(job.sim_req_mem,)
        script+="#SBATCH --qos=%s\n"%(job.sim_qosname,)
        script+="#SBATCH -p %s\n"%(job.sim_partition,)
        script+="#SBATCH -A %s\n"%(job.sim_account,)
        if not pd.isnull(job.sim_gres) and job.sim_gres!="":
            script+="#SBATCH --gres=%s\n"%(job.sim_gres,)
        if not pd.isnull(job.sim_shared):
            if job.sim_shared==0:
                script+="#SBATCH --exclusive\n"
        script+="sleep "+str(job.sim_duration)+"\n"
        
        with open(job.script_path,"wt") as fout:
            fout.write(script)
        shutil.chown(job.script_path,group="users")


def read_trace(trace_file_name):
    global trace
    trace=[]
    #simulator_start_time = math.ceil(time())
    with open(trace_file_name, "rt") as fin:
        for line in fin:
            event_command, event_details=line.split("|")
            event_command = event_command.strip().split()
            event_details = event_details.strip()

            dt = int(event_command[event_command.index("-dt")+1])
            etype = event_command[event_command.index("-e")+1]
            if etype=="submit_batch_job":
                etype = "SIM_SUBMIT_BATCH_JOB"
                sbatch = event_details
                # pull out --uid=user1
                m = re.search("--uid=([A-Za-z0-9]+)", sbatch)
                if m:
                    user = m.group(1)
                    sbatch = re.sub("--uid=[A-Za-z0-9]+", "", sbatch)
                else:
                    user = getpass.getuser()
                # pull out -sim-walltime 10
                m = re.search("-sim-walltime\s+([-0-9]+)", sbatch)
                if m:
                    walltime = int(m.group(1))
                    sbatch = re.sub("-sim-walltime\s+[-0-9]+", "", sbatch)
                else:
                    walltime = 365*24*3600

                # job id
                m = re.search("-jid\s+([0-9]+)", sbatch)
                if m:
                    job_id = "jobid_" + m.group(1)
                    sbatch = re.sub("-jid\s+[0-9]+", "", sbatch)
                else:
                    job_id = "jobid_None"

                # job name
                m = re.search("-J\s+(\S+)", sbatch)
                if not m:
                    sbatch = "-J " + job_id + " " + sbatch


                # pull out pseudo.job
                sbatch = sbatch.replace("pseudo.job", "/usr/local/miniapps/sleep.job %d" % walltime)


                payload = {
                    'user': user,
                    'walltime': walltime,
                    'sbatch': sbatch
                }
            else:
                payload = None

            trace.append({"dt":dt,"etype":etype,"payload":payload})

def run_slurm(args):
    #read trace
    read_trace(args.trace)
    ##
    #start all slurm daemons
    slurm_conf_loc=os.path.join(args.etc,'slurm.conf')
    slurmdbd_conf_loc=os.path.join(args.etc,'slurmdbd.conf')
    slurmd_loc=os.path.join(args.slurm,'sbin','slurmd')
    slurmdbd_loc=os.path.join(args.slurm,'sbin','slurmdbd')
    slurmctld_loc=os.path.join(args.slurm,'sbin','slurmctld')
    sbatch_loc=os.path.join(args.slurm,'bin','sbatch')
    sacctmgr_loc=os.path.join(args.slurm,'bin','sacctmgr')
    sacct_loc=os.path.join(args.slurm,'bin','sacct')
    sinfo_loc=os.path.join(args.slurm,'bin','sinfo')
    squeue_loc=os.path.join(args.slurm,'bin','squeue')
    monitor_loc=os.path.join(os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))),"monitor_slurm.sh")
    
    results_dir=os.path.abspath(args.results)
    results_perf_stat_loc=os.path.join(results_dir,'perf_stat.log')
    results_perf_profile_loc = os.path.join(results_dir, 'perf_profile.log')
    
    #check files presence
    if not os.path.isfile(slurm_conf_loc):
        raise Exception("Can not find slurm.conf at "+slurm_conf_loc)
    if not os.path.isfile(slurmdbd_conf_loc):
        raise Exception("Can not find slurmdbd.conf at "+slurmdbd_conf_loc)
    if not os.path.isfile(slurmd_loc):
        raise Exception("Can not find slurmd at "+slurmd_loc)
    if not os.path.isfile(slurmdbd_loc):
        raise Exception("Can not find slurmdbd at "+slurmdbd_loc)
    if not os.path.isfile(slurmctld_loc):
        raise Exception("Can not find slurmctld at "+slurmctld_loc)
    
    log.info("slurm.conf: "+slurm_conf_loc)
    log.info("slurmdbd: "+slurmdbd_loc)
    log.info("slurmd: "+slurmd_loc)
    log.info("slurmctld: "+slurmctld_loc)
    
    slurm_conf=slurm_conf_parser(slurm_conf_loc)
    slurmdbd_conf=slurm_conf_parser(slurmdbd_conf_loc)
    
    slurm_conf["SlurmdbdLogFile".lower()]=slurmdbd_conf["LogFile".lower()]
    
    SlurmUser=slurm_conf["SlurmUser".lower()]
    SlurmdUser=slurm_conf["SlurmdUser".lower()]
        
    if 'PidFile'.lower() in slurmdbd_conf:
        slurm_conf["SlurmdbdPidFile".lower()]=slurmdbd_conf["PidFile".lower()]
    
    #clean db
    if "StorageHost".lower() in slurmdbd_conf and args.delete:
        log.info("dropping db from previous runs")
        try:
            conn = pymysql.connect(host=slurmdbd_conf["StorageHost".lower()], 
                                   user=slurmdbd_conf["StorageUser".lower()], 
                                   passwd=slurmdbd_conf["StoragePass".lower()])
            cur = conn.cursor()
            
            trancate=[
                'DROP DATABASE IF EXISTS '+slurmdbd_conf['StorageLoc'.lower()]
            ]
            for t in trancate:
                print(t)
                cur.execute(t)
                cur.fetchall()
            cur.close()
            conn.close()
        except Exception as e:
            traceback.print_exc()
    
    #delete logs acct
    for filetype in ['JobCompLoc','SlurmctldLogFile',"SlurmdbdLogFile",'SlurmdLogFile',
                     "SlurmdPidFile","SlurmctldPidFile","SlurmdbdPidFile","sdiagMiniFileOut","SimStats","SlurmSchedLogFile"]:
        filetype_lower=filetype.lower()
        
        if filetype_lower in slurm_conf:
            if os.path.isfile(slurm_conf[filetype_lower]):
                if(args.delete):
                    log.info("deleting previous "+filetype+" file: "+slurm_conf[filetype_lower])
                    os.remove(slurm_conf[filetype_lower])
                else:
                    raise Exception("previous "+filetype+" file ("+slurm_conf[filetype_lower]+\
                                    ") is present on file-system. Can not continue simulation."+\
                                    "move it or run with flag -d to automatically delete it.")
            elif not os.path.isdir(os.path.dirname(slurm_conf[filetype_lower])):
                log.info("directory ("+os.path.dirname(slurm_conf[filetype_lower])+") does not exist, creating it ")
                #mkdir if needed
                os.makedirs(os.path.dirname(slurm_conf[filetype_lower]), mode=0o755)
            os.system("chown -R "+SlurmUser+":"+SlurmUser+" "+os.path.dirname(slurm_conf[filetype_lower]))
    #delete spool and state
    for filetype in ["StateSaveLocation","SlurmdSpoolDir"]:
        filetype_lower=filetype.lower()
        if filetype_lower in slurm_conf:
            if os.path.isdir(slurm_conf[filetype_lower]):
                if len(os.listdir(slurm_conf[filetype_lower]))>0:
                    if(args.delete):
                        log.info("deleting previous "+filetype+" files from "+slurm_conf[filetype_lower])
                        if slurm_conf[filetype_lower].count("state")>0 or slurm_conf[filetype_lower].count("spool")>0:
                            os.system("rm -r "+slurm_conf[filetype_lower]+"/*")
                        else:
                            raise Exception("directory for "+filetype+" is not empty ("+slurm_conf[filetype_lower]+\
                                        "). Can not continue simulation."+\
                                        "remove files from it.")
                    else:
                        raise Exception("directory for "+filetype+" is not empty ("+slurm_conf[filetype_lower]+\
                                        "). Can not continue simulation."+\
                                        "remove files from it or run with flag -d to automatically delete them.")
            else:
                log.info("directory ("+slurm_conf[filetype_lower]+") does not exist, creating it ")
                #mkdir if needed
                os.makedirs(slurm_conf[filetype_lower], mode=0o755)
            os.system("chown -R "+SlurmUser+":"+SlurmUser+" "+os.path.dirname(slurm_conf[filetype_lower]))
    
    #
    if os.path.exists(results_dir):
        if(args.delete):
            log.info("deleting previous results dir: "+results_dir)
            shutil.rmtree(results_dir)
        else:
            raise Exception("previous "+results_dir+" results directory is present on file-system. Can not continue simulation."+\
                            "move it or run with flag -d to automatically delete it.")
    os.makedirs(results_dir, mode=0o755, exist_ok=True)
    os.system("chown -R "+SlurmUser+":"+SlurmUser+" "+os.path.dirname(results_dir))
    os.chdir(results_dir)

    perf_profile = open(results_perf_profile_loc, "wt")
    
    #make nessesary directories
    #/var/state/
    start=time()
    
    global slurmdbd_out
    global slurmctld_out
    global slurmd_out
    
    slurmdbd_out=subprocess.DEVNULL
    slurmctld_out=subprocess.DEVNULL
    slurmd_out=subprocess.DEVNULL
    
    if args.octld!="":
        slurmctld_out=open(args.octld,"wt")
    if args.odbd!="":
        slurmdbd_out=open(args.odbd,"wt")  
    if args.od!="":
        slurmd_out=open(args.od,"wt")
    
    
    #start slurmdbd
    global slurmdbd_proc
    slurmdbd_proc=run_as_otheruser(SlurmUser,[slurmdbd_loc,'-Dvv'],env={'SLURM_CONF':slurm_conf_loc},
                                   stdout=slurmdbd_out,stderr=slurmdbd_out)
    #let the slurmdbd to spin-off
    sleep(5)
    
    #load accounting datals
    if args.acct_setup!="":
        sacctmgr_proc=run_as_otheruser(SlurmUser,sacctmgr_loc+' -i < '+args.acct_setup,
            env={'SLURM_CONF':slurm_conf_loc},shell=True)
        sacctmgr_proc.wait()
        
        sleep(1)
       

    
    #start slurmd
    global slurmd_proc
    if args.no_slurmd == False:
        slurmd_proc = run_as_otheruser(
            SlurmdUser,[slurmd_loc,'-Dvv'],env={'SLURM_CONF':slurm_conf_loc},
            stdout=slurmd_out,stderr=slurmd_out)
    #let the slurmd to spin-off
    sleep(1)
    
    #start slurmctrl
    global slurmctld_proc    
    slurmctld_proc=run_as_otheruser(SlurmUser,[slurmctld_loc,'-D'],env={'SLURM_CONF':slurm_conf_loc},
                                       stdout=slurmctld_out,stderr=slurmctld_out)
    #let the slurmctrl to spin-off
    sleep(5)

    # check that all nodes up
    ssinfo = subprocess.check_output([sinfo_loc],env={'SLURM_CONF':slurm_conf_loc}).decode("utf-8").splitlines()
    for sline in ssinfo[1:]:
        sfields = sline.split()
        if sfields[4]=="down":
            print("Nodes %s are down, resuming them" % sfields[5])
            print(subprocess.check_output(
                ['scontrol', "update", "NodeName="+sfields[5], "State=RESUME"]).decode("utf-8"))
    print(subprocess.check_output([sinfo_loc],env={'SLURM_CONF':slurm_conf_loc}).decode("utf-8"))
    
    #start monitor
    global monitor_proc    
    monitor_proc=run_as_otheruser(SlurmUser,[monitor_loc], env={'SLURM_CONF':slurm_conf_loc,'SLURM_HOME':args.slurm})
    
    #print("start slurmd now: "+slurmd_loc+' -Dvv')
    
    pslurmdbd = psutil.Process(pid=slurmdbd_proc.pid)
    pslurmctld = psutil.Process(pid=slurmctld_proc.pid)
    pslurmd = None if slurmd_proc is None else psutil.Process(pid=slurmd_proc.pid)

    log.info("Current time %s" % time())
    log.info("slurmdbd_create_time=%s" % pslurmdbd.create_time())
    log.info("slurmctld_create_time=%s" % pslurmctld.create_time())
    log.info("slurmd_create_time=%s" % (None if pslurmd is None else pslurmd.create_time()))

    last_realtime_proc_time = time()
    realtimestat = OrderedDict([
        ('time', last_realtime_proc_time),
        ('slurmdbd', get_process_realtimestat(pslurmdbd)),
        ('slurmd', get_process_realtimestat(pslurmd)),
        ('slurmctld', get_process_realtimestat(pslurmctld))
    ])
    perf_profile.write("[\n" + json.dumps(realtimestat, indent=" "))

    jobs_starts=pslurmctld.create_time()+args.dtstart

    perf_stat=OrderedDict([
        ('slurmdbd_create_time',
         datetime.datetime.fromtimestamp(pslurmdbd.create_time()).strftime(
             "%Y-%m-%dT%H:%M:%S.%f")),
        ('slurmctld_create_time',
         datetime.datetime.fromtimestamp(pslurmctld.create_time()).strftime(
             "%Y-%m-%dT%H:%M:%S.%f")),
        ('slurmd_create_time', None if pslurmd is None else datetime.datetime.fromtimestamp(
            pslurmd.create_time()).strftime(
             "%Y-%m-%dT%H:%M:%S.%f")),
        ('jobs_starts', jobs_starts),
        ('system_info', system_info())])
    with open(results_perf_stat_loc, "wt") as perf_stat_file:
        perf_stat_file.write(json.dumps(perf_stat, indent=" "))

    global trace

    for i in range(len(trace)):
        trace[i]['sim_submit_ts'] = jobs_starts + trace[i]['dt']
    ijob=0
    log.info("Starting job submittion")

    last_job_submit_time = time() + 2*365*24*3600
    try:
        while slurmctld_proc.poll() is None:
            if args.run_time>0 and time()-start>args.run_time:
                break
            now=time()
            Njobs=len(trace)
            # submit all jobs for which submit time is expired
            while ijob<Njobs and trace[ijob]['sim_submit_ts'] < now:
                user=trace[ijob]['payload']['user']
                sbatch_args=trace[ijob]['payload']['sbatch']
                #print("time to start"+str(trace.iloc[ijob]))
                #
                #
                #subprocess.run(cmd, shell=True)
                cmd="%s %s"%(sbatch_loc,sbatch_args)
                print("Executing: "+cmd+" For user "+user)
                sbatch_proc=run_as_otheruser(
                    user,cmd,env={'SLURM_CONF':slurm_conf_loc}, shell=True,
                    cwd="/home/" + user)
                sbatch_proc.wait()
                ijob+=1
                if ijob >= Njobs:
                    last_job_submit_time = time()
            if time()-last_realtime_proc_time > 60:
                last_realtime_proc_time = time()
                realtimestat = OrderedDict([
                    ('time', last_realtime_proc_time),
                    ('slurmdbd', get_process_realtimestat(pslurmdbd)),
                    ('slurmd', get_process_realtimestat(pslurmd)),
                    ('slurmctld', get_process_realtimestat(pslurmctld))
                ])
                perf_profile.write(",\n" + json.dumps((realtimestat), indent=" "))
            if last_job_submit_time + 30 < time():
                # i.e. all jobs are submitted
                if len(subprocess.check_output([squeue_loc], env={'SLURM_CONF':slurm_conf_loc}).splitlines()) <= 1:
                    perf_profile.write("\n]\n")
                    sleep(60)
                    break
            if ijob < Njobs:
                if trace[ijob]['sim_submit_ts']-time() > 0.2:
                    sleep(0.1)
            else:
                sleep(0.5)
    except:
        traceback.print_exc()
    #now keep waiting
    if args.run_time<0:
        log.info("All jobs submitted keep waiting...")
        while 1:
            sleep(1)
    if args.run_time==0:
        log.info("All jobs submitted wrapping up")
    else:
        if time()-start<args.run_time:
            log.info("All jobs submitted keep waiting...")
        while time()-start<args.run_time:
            sleep(1)
    
    
    slurmctld_run_time=time()-start
    if slurmctld_run_time <600.0:
        log.info("slurmctld took "+str(slurmctld_run_time)+" seconds to run.")
    elif slurmctld_run_time <2*3600.0:
        log.info("slurmctld took "+str(slurmctld_run_time/60.0)+" minutes to run.")
    else:
        log.info("slurmctld took "+str(slurmctld_run_time/3600.0)+" hours to run.")

    perf_stat["slurmctld_walltime"] = slurmctld_run_time
    with open(results_perf_stat_loc, "wt") as perf_stat_file:
        perf_stat_file.write(json.dumps(perf_stat, indent=" "))
    
    
    if monitor_proc!=None:
        monitor_proc.kill()
    
    #get sacct
    sacct_proc=run_as_otheruser(SlurmUser,sacct_loc + " --clusters " + slurm_conf["ClusterName".lower()] + """ --allusers \
    --parsable2 --allocations \
    --format jobid,jobidraw,cluster,partition,account,group,gid,\
user,uid,submit,eligible,start,end,elapsed,exitcode,state,nnodes,\
ncpus,reqcpus,reqmem,reqgres,timelimit,qos,nodelist,jobname,NTasks \
    --state CANCELLED,COMPLETED,FAILED,NODE_FAIL,PREEMPTED,TIMEOUT \
    --starttime 2015-09-01T00:00:00 > slurm_acct.out""",env={'SLURM_CONF':slurm_conf_loc}, shell=True)
    sacct_proc.wait()
    
    sleep(1)
    #copy results
    #copy files to results storage directory
    log.info("Copying results to :"+results_dir)
    
    resfiles={}
    for param in ['JobCompLoc','SlurmctldLogFile',"sdiagFileOut","sprioFileOut","SimStats","sinfoFileOut","squeueFileOut", "SlurmSchedLogFile"]:
        paraml=param.lower()
        if paraml in slurm_conf:
            log.info("copying resulting file "+slurm_conf[paraml]+" to "+results_dir)
            shutil.copy(slurm_conf[paraml],results_dir)
            resfiles[param]=os.path.join(results_dir,os.path.basename(slurm_conf[paraml]))
    

    
    if slurmdbd_proc!=None:
        slurmdbd_proc.kill()
    if slurmctld_proc!=None:
        slurmctld_proc.kill()
    if slurmd_proc!=None:
        slurmd_proc.kill()
    
    
    if slurmctld_out!=None and slurmctld_out!=subprocess.DEVNULL:
        slurmctld_out.close()
    if slurmdbd_out!=None and slurmdbd_out!=subprocess.DEVNULL:
        slurmdbd_out.close()
    if slurmd_out!=None and slurmd_out!=subprocess.DEVNULL:
        slurmd_out.close()
        
    log.info("Done")


if __name__ == '__main__':
    
    import argparse
        
    parser = argparse.ArgumentParser(description='Slurm Run automation')
    
    parser.add_argument('-s', '--slurm', required=True, type=str,
        help="top directory of slurm installation")
    parser.add_argument('-e', '--etc', required=True, type=str,
        help="etc directory for current simulation")
    parser.add_argument('-t', '--trace', required=True, type=str,
        help="job trace events file")
    parser.add_argument('-d', '--delete', action='store_true', 
            help="delete files from previous simulation")
    parser.add_argument('-nc', '--no-slurmctld', action='store_true', 
            help="do not start slurmctld")
    parser.add_argument('-nd', '--no-slurmd', action='store_true',
            help="do not start slurmd")
    parser.add_argument('-octld', '--octld', required=False, type=str, default="",
            help="redirect stdout and stderr of slurmctld to octrd")
    parser.add_argument('-odbd', '--odbd', required=False, type=str, default="",
            help="redirect stdout and stderr of slurmdbd to odbd")
    parser.add_argument('-od', '--od', required=False, type=str, default="",
            help="redirect stdout and stderr of slurmd to od")
    parser.add_argument('-dtstart', '--dtstart', required=False, type=int, default=30,
            help="seconds before first job")
    parser.add_argument('-a', '--acct-setup', required=False, type=str, default="",
            help="script for sacctmgr to setup accounts")
    parser.add_argument('-rt', '--run-time', required=False, type=int, default=0,
            help="total time for slurm to run in seconds, -1 run forever, 0 till last job is done, >0 seconds to run")
    parser.add_argument('-r', '--results', required=False, type=str, default="results",
            help="copy results to that directory")
    parser.add_argument('-v', '--verbose', action='store_true', 
        help="turn on verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        log.basicConfig(level=log.DEBUG,format='[%(asctime)s]-[%(levelname)s]: %(message)s')
    else:
        log.basicConfig(level=log.INFO,format='[%(asctime)s]-[%(levelname)s]: %(message)s')
    
    signal.signal(signal.SIGINT, signal_handler)
    run_slurm(args)
    