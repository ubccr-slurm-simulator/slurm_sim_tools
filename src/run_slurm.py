#!/usr/bin/env python3
import os
import sys
import subprocess
import logging as log
import pprint
import shutil
import pymysql
import pwd
import signal
import pandas as pd
import traceback
import inspect
from time import sleep,time

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
    env[ 'HOME'     ]  = user_home_dir
    env[ 'LOGNAME'  ]  = username
    env[ 'PWD'      ]  = cwd  if 'cwd' not in kwargs else kwargs['env']
    env[ 'USER'     ]  = username
    if 'env' in kwargs:
        env.update(kwargs['env'])
    kwargs['env']=env
    
    kwargs['preexec_fn']=demote(user_uid, user_gid)
    
    if 'cwd' not in kwargs:
        kwargs['cwd']=cwd
    
    
    process = subprocess.Popen(
        args, **kwargs
    )
    return process

def slurm_conf_parser(slurm_conf_loc):
    """very simple parser to get some parameters from slurm.conf"""
    if not os.path.isfile(slurm_conf_loc):
        raise Exception("Can not find slurm.conf at "+slurm_conf_loc)
    
    params={}
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

def read_trace_and_prep_scripts(trace_file_name):
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
    

def run_slurm(args):
    
    #read trace
    read_trace_and_prep_scripts(args.trace)
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
    monitor_loc=os.path.join(os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))),"monitor_slurm.sh")
    
    results_dir=os.path.abspath(args.results)
    
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
    slurmd_proc=subprocess.Popen([slurmd_loc,'-Dvv'],env={'SLURM_CONF':slurm_conf_loc},
                                   stdout=slurmd_out,stderr=slurmd_out)
    #let the slurmd to spin-off
    sleep(1)
    
    #start slurmctrl
    global slurmctld_proc    
    slurmctld_proc=run_as_otheruser(SlurmUser,[slurmctld_loc,'-D'],env={'SLURM_CONF':slurm_conf_loc},
                                       stdout=slurmctld_out,stderr=slurmctld_out)
    #let the slurmctrl to spin-off
    sleep(5)
    
    #start monitor
    global monitor_proc    
    monitor_proc=run_as_otheruser(SlurmUser,[monitor_loc],env={'SLURM_CONF':slurm_conf_loc})
    
    #print("start slurmd now: "+slurmd_loc+' -Dvv')
    


    jobs_starts=int(time()+args.dtstart)
    global trace
    trace.sim_submit_ts+=jobs_starts
    ijob=0
    log.info("Starting job submittion")
    
    try:
        while slurmctld_proc.poll() is None:
            if args.run_time>0 and time()-start>args.run_time:
                break
            now=time()
            Njobs=trace.shape[0]
            while ijob<Njobs and trace.sim_submit_ts.iloc[ijob] < now:
                user=trace.sim_username.iloc[ijob]
                script_path=trace.script_path.iloc[ijob]
                #print("time to start"+str(trace.iloc[ijob]))
                #
                #
                #subprocess.run(cmd, shell=True)
                cmd="%s %s"%(sbatch_loc,script_path)
                print("Executing: "+cmd+" For user "+user)
                sbatch_proc=run_as_otheruser(user,cmd,env={'SLURM_CONF':slurm_conf_loc}, shell=True)
                sbatch_proc.wait()
                ijob+=1
            sleep(0.5)
    except:
        traceback.print_exc()
    #now keep waiting
    log.info("All jobs submittes keep waiting...")
    if args.run_time<=0:
        while 1:
            sleep(1)
    else:
        while time()-start<args.run_time:
            sleep(1)
    
    
    slurmctld_run_time=time()-start
    if slurmctld_run_time <600.0:
        log.info("slurmctld took "+str(slurmctld_run_time)+" seconds to run.")
    elif slurmctld_run_time <2*3600.0:
        log.info("slurmctld took "+str(slurmctld_run_time/60.0)+" minutes to run.")
    else:
        log.info("slurmctld took "+str(slurmctld_run_time/3600.0)+" hours to run.")
        
    
    
    if monitor_proc!=None:
        monitor_proc.kill()
    
    #get sacct
    sacct_proc=run_as_otheruser(SlurmUser,sacct_loc+""" --clusters micro --allusers \
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
    for param in ['JobCompLoc','SlurmctldLogFile',"sdiagFileOut","sprioFileOut","SimStats","sinfoFileOut","squeueFileOut"]:
        paraml=param.lower()
        if paraml in slurm_conf:
            log.info("copying resulting file "+slurm_conf[paraml]+" to "+results_dir)
            shutil.copy(slurm_conf[paraml],results_dir)
            resfiles[param]=os.path.join(results_dir,os.path.basename(slurm_conf[paraml]))
    

    
    if slurmdbd_proc!=None:
        slurmdbd_proc.kill()
    if slurmctld_proc!=None:
        slurmctld_proc.kill()
    if slurmctld_proc!=None:
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
        help="job trace csv file")
    parser.add_argument('-d', '--delete', action='store_true', 
            help="delete files from previous simulation")
    parser.add_argument('-nc', '--no-slurmctld', action='store_true', 
            help="do not start slurmctld just clean-up and start slurmdbd")
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
            help="total time for slurm to run in seconds")
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
    