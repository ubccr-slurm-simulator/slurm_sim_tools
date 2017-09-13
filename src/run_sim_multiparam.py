#!/usr/bin/env python3
import os
import sys
import subprocess
import logging as log
import pprint
import shutil
import pymysql
import signal
import numpy
from time import sleep,time
from email.policy import default

from run_sim import slurm_conf_parser,kill_all_slurm_daemons,run_sim

sim_conf_loc=None
sim_conf_template_loc=None
sim_conf_back_loc=None

def signal_handler(m_signal, frame):
    print('Ctrl+C intercepted, exiting...')
    kill_all_slurm_daemons()
    if sim_conf_back_loc!=None:
        shutil.copyfile(sim_conf_back_loc,sim_conf_loc)
    sys.exit(0)

def get_value_for_param_from_slurm_confline(slurm_confline,param):
    l=slurm_confline.strip()
    if len(l)==0:
        return None
    if l[0]=='#':
        return None
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
        if name==param:
            return value
    return None

def run_sim_multiparam(args):
    global sim_conf_loc
    global sim_conf_template_loc
    global sim_conf_back_loc
    
    sim_param=args.sim_param
    values=eval(args.values)
    log.info("Parameter to alter:"+str(sim_param))
    log.info("Values: "+str(values))
    
    slurm_conf_loc=os.path.join(args.etc,'slurm.conf')
    if not os.path.isfile(slurm_conf_loc):
        raise Exception("Can not find slurm.conf at "+slurm_conf_loc)
    slurm_conf=slurm_conf_parser(slurm_conf_loc)
    
    sim_conf_loc=os.path.join(args.etc,'sim.conf')
    if not os.path.isfile(sim_conf_loc):
        raise Exception("Can not find sim.conf at "+slurm_conf_loc)
    sim_conf_template_loc=os.path.join(args.etc,'sim_template.conf')
    sim_conf_back_loc=os.path.join(args.etc,'sim_back.conf')
    shutil.copyfile(sim_conf_loc,sim_conf_back_loc)
    shutil.copyfile(sim_conf_loc,sim_conf_template_loc)
    
    with open(sim_conf_template_loc,"rt") as fin:
        sim_conf_lines=fin.readlines()
    
    results_topdir=args.results
    for v in values:
        log.info("working on value: "+str(v))
        
        sim_conf=""
        for l in sim_conf_lines:
            v2=get_value_for_param_from_slurm_confline(l,sim_param)
            if v2 is None:
                sim_conf+=l
            else:
                sim_conf+="#altered by run_sim_multiparam\n"
                sim_conf+=sim_param+" = "+str(v)+"\n"
        with open(sim_conf_loc,"wt") as fout:
            fout.write(sim_conf)
        
        args.results=results_topdir+"/"+str(sim_param)+"_"+str(v)
        
        run_sim(args)

    shutil.copyfile(sim_conf_back_loc,sim_conf_loc)
    

if __name__ == '__main__':
    
    import argparse
        
    parser = argparse.ArgumentParser(description='Slurm Simulator Run automation')
    
    parser.add_argument('-s', '--slurm', required=True, type=str,
        help="top directory of slurm installation")
    parser.add_argument('-e', '--etc', required=True, type=str,
        help="etc directory for current simulation")
    parser.add_argument('-d', '--delete', action='store_true', 
            help="delete files from previous simulation")
    parser.add_argument('-nc', '--no-slurmctld', action='store_true', 
            help="do not start slurmctld just clean-up and start slurmdbd")
    parser.add_argument('-octld', '--octld', required=False, type=str, default="",
            help="redirect stdout and stderr of slurmctld to octrd")
    parser.add_argument('-odbd', '--odbd', required=False, type=str, default="",
            help="redirect stdout and stderr of slurmdbd to odbd")
    parser.add_argument('-v', '--verbose', action='store_true', 
        help="turn on verbose logging")
    parser.add_argument('-r', '--results', required=False, type=str, default="results",
            help="copy results to that directory")
    parser.add_argument('--sim-param', required=False, type=str, default="",
        help="turn on verbose logging")
    parser.add_argument('--values', required=True, type=str, default="",
        help="turn on verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        log.basicConfig(level=log.DEBUG,format='[%(asctime)s]-[%(levelname)s]: %(message)s')
    else:
        log.basicConfig(level=log.INFO,format='[%(asctime)s]-[%(levelname)s]: %(message)s')
    
    signal.signal(signal.SIGINT, signal_handler)
    run_sim_multiparam(args)
    #
    #run_sim(args)
    