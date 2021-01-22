#!/usr/bin/env python3
import os
import sys
import subprocess
import logging as log
import pprint
import shutil
import pymysql
import signal
import getpass
from time import sleep,time
import psutil
import json
from collections import OrderedDict
from process_sprio import process_sprio
from process_simstat import process_simstat

from sperf import get_process_realtimestat, system_info

slurmdbd_proc=None
slurmdbd_out=None
slurmctld_proc=None
slurmctld_out=None
shared_memory_name=None

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

def kill_all_slurm_daemons():
    print('Ctrl+C intercepted, exiting...')
    if slurmdbd_proc!=None:
        slurmdbd_proc.kill()
    if slurmctld_proc!=None:
        slurmctld_proc.kill()
    if slurmctld_out!=None:
        slurmctld_out.close()
    if slurmdbd_out!=None:
        slurmdbd_out.close()    
    if shared_memory_name!=None:
        filename="/dev/shm"+shared_memory_name
        if os.path.exists(filename):
            os.remove(filename)
    
def signal_handler(m_signal, frame):
    print('Ctrl+C intercepted, exiting...')
    kill_all_slurm_daemons()
    sys.exit(0)
    
def check_slurm_conf(slurm_conf,slurm_etc,slurm_bin_top,slurmdbd_conf):
    error_count=0
    warning_count=0
    
    log.info("Checking slurm.conf")
    
    #check that PluginDir points to slurm_bin_top
    if "PluginDir".lower() in slurm_conf:
        if os.path.abspath(slurm_conf["PluginDir".lower()]) !=  os.path.abspath(os.path.join(slurm_bin_top,"lib","slurm")):
            error_count+=1
            log.error("PluginDir from slurm.conf (%s) does not match provided slurm binary path(%s)!"%(
                os.path.abspath(slurm_conf["PluginDir".lower()]),  os.path.abspath(os.path.join(slurm_bin_top,"lib","slurm"))))
            
    else:
        error_count+=1
        log.error("PluginDir from slurm.conf is not set, set it to: "+os.path.abspath(os.path.join(slurm_bin_top,"lib","slurm")))
    
    
    #AuthType=auth/none
    if "AuthType".lower() in slurm_conf:
        if slurm_conf["AuthType".lower()]!="auth/none":
            error_count+=1
            log.error("For simulation AuthType should be set to auth/none in slurm.conf!\n"+\
                      "   In simulation there is no need for good authentication")
    else:
        error_count+=1
        log.error("For simulation AuthType should be set to auth/none in slurm.conf!")
    #ControlMachine=localhost
    if "ControlMachine".lower() in slurm_conf:
        if slurm_conf["ControlMachine".lower()]!="localhost":
            error_count+=1
            log.error("For simulation ControlMachine from slurm.conf should be localhost not %s!"%(slurm_conf["ControlMachine".lower()],))
    else:
        error_count+=1
        log.error("For simulation ControlMachine should be set to localhost in slurm.conf!")
    
    #ControlAddr=localhost
    if "ControlAddr".lower() in slurm_conf:
        if slurm_conf["ControlAddr".lower()]!="localhost":
            error_count+=1
            log.error("For simulation ControlAddr from slurm.conf should be localhost not %s!"%(slurm_conf["ControlAddr".lower()],))
    else:
        error_count+=1
        log.error("For simulation ControlAddr should be set to localhost in slurm.conf!")
        
    #SlurmUser=slurm
    if "SlurmUser".lower() in slurm_conf:
        if slurm_conf["SlurmUser".lower()]!=getpass.getuser():
            error_count+=1
            log.error("For simulation SlurmUser should be set to %s in slurm.conf!"%(getpass.getuser(),))
    else:
        error_count+=1
        log.error("For simulation SlurmUser should be set to %s in slurm.conf!"%(getpass.getuser(),))
        
    #CryptoType=crypto/openssl
    if "CryptoType".lower() in slurm_conf:
        if slurm_conf["CryptoType".lower()]!="crypto/openssl":
            error_count+=1
            log.error("For simulation CryptoType should be set to crypto/openssl!")
    else:
        error_count+=1
        log.error("For simulation CryptoType should be set to crypto/openssl!")
        
    #JobCompType=jobcomp/filesacctout
    if "JobCompType".lower() in slurm_conf:
        if slurm_conf["JobCompType".lower()]!="jobcomp/filesacctout":
            error_count+=1
            log.error("For simulation JobCompType should be set to jobcomp/filesacctout, it provides sacct like output which is easy for loading in R!")
    else:
        error_count+=1
        log.error("For simulation JobCompType should be set to jobcomp/filesacctout,  it provides sacct like output which is easy for loading in R!")
    
    #FrontendName=localhost
    if "FrontendName".lower() in slurm_conf:
        if slurm_conf["FrontendName".lower()]!="localhost":
            error_count+=1
            log.error("For simulation FrontendName should be set to localhost!")
    else:
        error_count+=1
        log.error("For simulation FrontendName should be set to localhost!")
    
    #AccountingStorageType=accounting_storage/slurmdbd
    #AccountingStorageHost=localhost
    if "AccountingStorageType".lower() in slurm_conf:
        if slurm_conf["AccountingStorageType".lower()]=="accounting_storage/slurmdbd":
            if "AccountingStorageHost".lower() not in slurm_conf:
                error_count+=1
                log.error("For simulation AccountingStorageHost should be set to localhost!")
            else:
                if slurm_conf["AccountingStorageHost".lower()]!="localhost":
                    error_count+=1
                    log.error("For simulation AccountingStorageHost (currently set to "+slurm_conf["AccountingStorageHost".lower()]+") should be set to localhost!")
    else:
        error_count+=1
        log.error("AccountingStorageType is not set!")
    
    #check that slurmdbd ports matches on in slurm.conf DefaultStoragePort=29001
    if "DefaultStoragePort".lower() in slurm_conf and "DbdPort".lower() in slurmdbd_conf:
        if slurm_conf["DefaultStoragePort".lower()]!=slurmdbd_conf["DbdPort".lower()]:
             error_count+=1
             log.error("DefaultStoragePort (%s) should match DbdPort (%s) but it does not!"%(slurm_conf["DefaultStoragePort".lower()],slurmdbd_conf["DbdPort".lower()]))

    return error_count


def check_slurmdbd_conf(slurmdbd_conf,slurm_etc,slurm_bin_top):
    error_count=0
    warning_count=0
    
    log.info("Checking slurmdbd.conf")
    
    #check that PluginDir points to slurm_bin_top
    if "PluginDir".lower() in slurmdbd_conf:
        if os.path.abspath(slurmdbd_conf["PluginDir".lower()]) !=  os.path.abspath(os.path.join(slurm_bin_top,"lib","slurm")):
            error_count+=1
            log.error("PluginDir from slurm.conf (%s) does not match provided slurm binary path(%s)!"%(
                os.path.abspath(slurmdbd_conf["PluginDir".lower()]),  os.path.abspath(os.path.join(slurm_bin_top,"lib","slurm"))))
            
    else:
        error_count+=1
        log.error("PluginDir from slurm.conf is not set, the default value is /usr/local/lib/slurm")
    
    #AuthType=auth/none
    if "AuthType".lower() in slurmdbd_conf:
        if slurmdbd_conf["AuthType".lower()]!="auth/none":
            error_count+=1
            log.error("For simulation AuthType should be set to auth/none in slurm.conf!\n"+\
                      "   In simulation there is no need for good authentication")
    else:
        error_count+=1
        log.error("For simulation AuthType should be set to auth/none in slurm.conf!")
    
    #DbdHost=localhost
    if "DbdHost".lower() in slurmdbd_conf:
        if slurmdbd_conf["DbdHost".lower()]!="localhost":
            error_count+=1
            log.error("For simulation DbdHost should be set to localhost!")
    else:
        error_count+=1
        log.error("For simulation DbdHost should be set to localhost!")
    
    if "StorageType".lower() in slurmdbd_conf:
        if slurmdbd_conf["StorageType".lower()]=="accounting_storage/mysql":
            if "StorageHost".lower() not in slurmdbd_conf:
                error_count+=1
                log.error("For simulation StorageHost should be set to localhost!")
            else:
                if slurmdbd_conf["StorageHost".lower()]!="localhost":
                    error_count+=1
                    log.error("For simulation StorageHost should be set to localhost!")
    else:
        error_count+=1
        log.error("StorageType is not set!")
    
    #SlurmUser=slurm
    if "SlurmUser".lower() in slurmdbd_conf:
        if slurmdbd_conf["SlurmUser".lower()]!=getpass.getuser():
            error_count+=1
            log.error("For simulation SlurmUser should be set to %s in slurm.conf!"%(getpass.getuser(),))
    else:
        error_count+=1
        log.error("For simulation SlurmUser should be set to %s in slurm.conf!"%(getpass.getuser(),))
        
    return error_count

def check_sim_conf(sim_conf,slurm_etc,slurm_bin_top):
    error_count=0
    warning_count=0
    
    log.info("Checking sim.conf")
    
    return error_count

def run_sim(args):
    
    slurm_conf_loc=os.path.join(args.etc,'slurm.conf')
    slurmdbd_conf_loc=os.path.join(args.etc,'slurmdbd.conf')
    sim_conf_loc=os.path.join(args.etc,'sim.conf')
    slurmdbd_loc=os.path.join(args.slurm,'sbin','slurmdbd')
    slurmctld_loc=os.path.join(args.slurm,'sbin','slurmctld')
    sbatch_loc=os.path.join(args.slurm,'bin','sbatch')
    sacctmgr_loc=os.path.join(args.slurm,'bin','sacctmgr')
    sacct_loc=os.path.join(args.slurm,'bin','sacct')
    sinfo_loc=os.path.join(args.slurm,'bin','sinfo')
    squeue_loc=os.path.join(args.slurm,'bin','squeue')

    results_dir=os.path.abspath(args.results)
    results_perf_stat_loc=os.path.join(results_dir,'perf_stat.log')
    results_perf_profile_loc = os.path.join(results_dir, 'perf_profile.log')

    #check files presence
    if not os.path.isfile(slurm_conf_loc):
        raise Exception("Can not find slurm.conf at "+slurm_conf_loc)
    if not os.path.isfile(slurmdbd_conf_loc):
        raise Exception("Can not find slurmdbd.conf at "+slurmdbd_conf_loc)
    if not os.path.isfile(slurmdbd_loc):
        raise Exception("Can not find slurmdbd at "+slurmdbd_loc)
    if not os.path.isfile(slurmctld_loc):
        raise Exception("Can not find slurmctld at "+slurmctld_loc)
    
    log.info("slurm.conf: "+slurm_conf_loc)
    log.info("slurmdbd: "+slurmdbd_loc)
    log.info("slurmctld: "+slurmctld_loc)
    
    slurm_conf=slurm_conf_parser(slurm_conf_loc)
    slurmdbd_conf=slurm_conf_parser(slurmdbd_conf_loc)
    sim_conf=slurm_conf_parser(sim_conf_loc)
    
    slurm_conf.update(sim_conf)
    
    global shared_memory_name
    if "SharedMemoryName".lower() in sim_conf:
        shared_memory_name=sim_conf["SharedMemoryName".lower()]
    else:
        shared_memory_name="/slurm_sim.shm"
        
    if 'PidFile'.lower() in slurmdbd_conf:
        slurm_conf["SlurmdbdPidFile".lower()]=slurmdbd_conf["PidFile".lower()]
    
    #clean db
    if "StorageHost".lower() in slurmdbd_conf and args.delete:
        log.info("trancating db from previous runs")
        conn = pymysql.connect(host=slurmdbd_conf["StorageHost".lower()], 
                               user=slurmdbd_conf["StorageUser".lower()], 
                               passwd=slurmdbd_conf["StoragePass".lower()])
        cur = conn.cursor()
        
        trancate=[
            'DROP DATABASE IF EXISTS '+slurmdbd_conf['StorageLoc'.lower()]
            # 'TRUNCATE TABLE `'+slurm_conf['clustername']+'_assoc_usage_day_table`',
            # 'TRUNCATE TABLE `'+slurm_conf['clustername']+'_assoc_usage_hour_table`',
            # 'TRUNCATE TABLE `'+slurm_conf['clustername']+'_assoc_usage_month_table`',
            # 'TRUNCATE TABLE `'+slurm_conf['clustername']+'_event_table`',
            # 'TRUNCATE TABLE `'+slurm_conf['clustername']+'_job_table`',
            # 'TRUNCATE TABLE `'+slurm_conf['clustername']+'_last_ran_table`',
            # 'TRUNCATE TABLE `'+slurm_conf['clustername']+'_resv_table`',
            # 'TRUNCATE TABLE `'+slurm_conf['clustername']+'_step_table`',
            # 'TRUNCATE TABLE `'+slurm_conf['clustername']+'_suspend_table`',
            # 'TRUNCATE TABLE `'+slurm_conf['clustername']+'_usage_day_table`',
            # 'TRUNCATE TABLE `'+slurm_conf['clustername']+'_usage_hour_table`'
        ]
        for t in trancate:
            print(t)
            cur.execute(t)
            cur.fetchall()
        cur.close()
        conn.close()
    
    #delete logs acct
    for filetype in ['JobCompLoc','SlurmctldLogFile',"SlurmdbdLogFile",'SlurmdLogFile','SlurmSchedLogFile',
                     "SlurmdPidFile","SlurmctldPidFile","SlurmdbdPidFile","sdiagFileOut","sprioFileOut","SimStats",
                     "sinfoFileOut","squeueFileOut"]:
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
    
    if shared_memory_name!=None:
        filename="/dev/shm"+shared_memory_name
        if os.path.exists(filename):
            if(args.delete):
                log.info("deleting previous shared memory: "+filename)
                os.remove(filename)
            else:
                raise Exception("shared memory from previous run still on system ("+filename+").Can not continue simulation."+\
                                "remove files from it or run with -d to automatically delete files from previous simulation.")
    # remove previous results
    if os.path.exists(results_dir):
        if(args.delete):
            log.info("deleting previous results dir: "+results_dir)
            shutil.rmtree(results_dir)
        else:
            raise Exception("previous "+results_dir+" results directory is present on file-system. Can not continue simulation."+\
                            "move it or run with flag -d to automatically delete it.")

    #check conf
    errors_in_conf=0
    errors_in_conf+=check_slurm_conf(slurm_conf,args.etc,args.slurm,slurmdbd_conf)
    errors_in_conf+=check_slurmdbd_conf(slurmdbd_conf,args.etc,args.slurm)
    errors_in_conf+=check_sim_conf(sim_conf,args.etc,args.slurm)
    
    if errors_in_conf>0 and args.ignore_errors_in_conf==False:
        exit(1)

    # create results dir
    os.makedirs(results_dir, mode=0o755, exist_ok=True)
    os.chdir(results_dir)
    perf_profile = open(results_perf_profile_loc, "wt")
    
    #start slurmdbd
    global slurmdbd_proc
    global slurmdbd_out
    
    if args.odbd=="":
        slurmdbd_proc=subprocess.Popen([slurmdbd_loc,'-Dvv'],env={'SLURM_CONF':slurm_conf_loc},
                                       stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    else:
        slurmdbd_out=open(args.odbd,"wt")
        slurmdbd_proc=subprocess.Popen([slurmdbd_loc,'-Dvv'],env={'SLURM_CONF':slurm_conf_loc},
                                       stdout=slurmdbd_out,stderr=slurmdbd_out)
    #let the slurmdbd to spin-off
    sleep(5)

    #load accounting datals
    if args.acct_setup!="":
        sacctmgr_proc=subprocess.Popen(sacctmgr_loc+' -i < '+args.acct_setup,
            env={'SLURM_CONF':slurm_conf_loc},shell=True)
        sacctmgr_proc.wait()

        sleep(1)

    #start slurmctrl
    global slurmctld_proc
    global slurmctld_out
    
    start=time()
    if args.no_slurmctld==False:
        
        if args.octld=="":
            slurmctld_proc=subprocess.Popen([slurmctld_loc,'-D'],env={'SLURM_CONF':slurm_conf_loc},
                                       stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        else:
            slurmctld_out=open(args.octld,"wt")
            slurmctld_proc=subprocess.Popen([slurmctld_loc,'-D'],env={'SLURM_CONF':slurm_conf_loc},
                                       stdout=slurmctld_out,stderr=slurmctld_out)
        last_realtime_proc_time = time()
        pslurmdbd = psutil.Process(pid=slurmdbd_proc.pid)
        pslurmctld = psutil.Process(pid=slurmctld_proc.pid)
        realtimestat = OrderedDict([
            ('time', last_realtime_proc_time),
            ('slurmdbd', get_process_realtimestat(pslurmdbd)),
            ('slurmd', None),
            ('slurmctld', get_process_realtimestat(pslurmctld))
        ])
        perf_profile.write("[\n" + json.dumps(realtimestat, indent=" "))
        jobs_starts=int(pslurmctld.create_time()+args.dtstart)
        perf_stat=OrderedDict([
            ('slurmdbd_create_time', pslurmdbd.create_time()),
            ('slurmctld_create_time', pslurmctld.create_time()),
            ('slurmd_create_time', None),
            ('jobs_starts', jobs_starts),
            ('system_info', system_info())])
        with open(results_perf_stat_loc, "wt") as perf_stat_file:
            perf_stat_file.write(json.dumps(perf_stat, indent=" "))

        sleep(1)
        while slurmctld_proc.poll() is None:
            if time()-last_realtime_proc_time > 60:
                last_realtime_proc_time = time()
                realtimestat = OrderedDict([
                    ('time', last_realtime_proc_time),
                    ('slurmdbd', get_process_realtimestat(pslurmdbd)),
                    ('slurmd', None),
                    ('slurmctld', get_process_realtimestat(pslurmctld))
                ])
                perf_profile.write(",\n" + json.dumps((realtimestat), indent=" "))
            sleep(1)
        slurmctld_run_time=time()-start
        if slurmctld_run_time <600.0:
            log.info("slurmctld took "+str(slurmctld_run_time)+" seconds to run.")
        elif slurmctld_run_time <2*3600.0:
            log.info("slurmctld took "+str(slurmctld_run_time/60.0)+" minutes to run.")
        else:
            log.info("slurmctld took "+str(slurmctld_run_time/3600.0)+" hours to run.")

        perf_profile.write("\n]\n")
        perf_stat["slurmctld_walltime"] = slurmctld_run_time
        with open(results_perf_stat_loc, "wt") as perf_stat_file:
            perf_stat_file.write(json.dumps(perf_stat, indent=" "))
    else:
        sleep(1)
        log.info("you can start slurmctld now")
        while 1:
            sleep(1)
    
    if slurmdbd_proc!=None:
        slurmdbd_proc.kill()
        slurmdbd_proc=None
    if slurmctld_proc!=None:
        slurmctld_proc.kill()
        slurmctld_proc=None
    
    if slurmctld_out!=None:
        slurmctld_out.close()
        slurmctld_out=None
    if slurmdbd_out!=None:
        slurmdbd_out.close()
        slurmdbd_out=None
    
    if shared_memory_name!=None:
        filename="/dev/shm"+shared_memory_name
        if os.path.exists(filename):
            os.remove(filename)
    log.info("Done with simulation")
    
    #copy files to results storage directory
    log.info("Copying results to :"+results_dir)

    resfiles={}
    for param in ['JobCompLoc','SlurmctldLogFile',"sdiagFileOut","sprioFileOut","SimStats","sinfoFileOut","squeueFileOut", "SlurmSchedLogFile"]:
        paraml=param.lower()
        if paraml in slurm_conf:
            log.info("copying resulting file "+slurm_conf[paraml]+" to "+results_dir)
            shutil.copy(slurm_conf[paraml],results_dir)
            resfiles[param]=os.path.join(results_dir,os.path.basename(slurm_conf[paraml]))
    #process some of the outputs
    if "sprioFileOut" in resfiles:
        csv=os.path.join(results_dir,"sprio.csv")
        log.info("processing "+resfiles['sprioFileOut']+" to "+csv)
        process_sprio(resfiles['sprioFileOut'], csv)
    if "SimStats" in resfiles:
        simstat_backfill_csv=os.path.join(results_dir,"simstat_backfill.csv")
        log.info("processing "+resfiles['SimStats']+" to "+simstat_backfill_csv)
        process_simstat(resfiles['SimStats'], simstat_backfill_csv)    
        
    log.info("Done")


if __name__ == '__main__':
    
    import argparse
        
    parser = argparse.ArgumentParser(description='Slurm Simulator Run automation')
    
    parser.add_argument('-s', '--slurm', required=True, type=str,
        help="top directory of slurm installation")
    parser.add_argument('-e', '--etc', required=True, type=str,
        help="etc directory for current simulation")
    parser.add_argument('-t', '--trace', required=True, type=str,
                        help="job trace events file")
    parser.add_argument('-a', '--acct-setup', required=False, type=str, default="",
            help="script for sacctmgr to setup accounts")
    parser.add_argument('-dtstart', '--dtstart', required=False, type=int,
                        default=30,
                        help="seconds before first job")
    parser.add_argument('-d', '--delete', action='store_true', 
            help="delete files from previous simulation")
    parser.add_argument('-nc', '--no-slurmctld', action='store_true', 
            help="do not start slurmctld just clean-up and start slurmdbd")
    parser.add_argument('-octld', '--octld', required=False, type=str, default="",
            help="redirect stdout and stderr of slurmctld to octrd")
    parser.add_argument('-odbd', '--odbd', required=False, type=str, default="",
            help="redirect stdout and stderr of slurmdbd to odbd")
    
    parser.add_argument('-r', '--results', required=False, type=str, default="results",
            help="copy results to that directory")
    
    parser.add_argument('--ignore-errors-in-conf', action='store_true', 
            help="try simulation even if there are errors configuration files")
    
    parser.add_argument('-v', '--verbose', action='store_true', 
        help="turn on verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        log.basicConfig(level=log.DEBUG,format='[%(asctime)s]-[%(levelname)s]: %(message)s')
    else:
        log.basicConfig(level=log.INFO,format='[%(asctime)s]-[%(levelname)s]: %(message)s')
    
    signal.signal(signal.SIGINT, signal_handler)
    run_sim(args)
    