#!/usr/bin/env python3
import os
import sys
import subprocess
import logging as log
import pprint
import shutil
import pymysql
import signal
from time import sleep,time
from process_sprio import process_sprio
from process_simstat import process_simstat


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

def cp_slurm_conf_dir(args):
    old_etc=os.path.abspath(args.old_etc)
    slurm_bin=os.path.abspath(args.slurm_bin)
    new_slurm_topdir=os.path.abspath(args.new_slurm_topdir)
    new_slurm_etc=os.path.join(args.new_slurm_topdir,"etc")
    overwrite=args.overwrite
    
    
    if not os.path.isdir(old_etc):
        raise Exception("Directory "+old_etc+" does not exist")
    if not os.path.isfile(os.path.join(old_etc,'slurm.conf')):
        raise Exception("Directory "+old_etc+" does not contain slurm.conf")
    if not overwrite and os.path.isdir(new_slurm_topdir):
        raise Exception("Directory "+new_slurm_topdir+" already exists, would not overwrite it!")
    
    log.info("Creating directory: "+new_slurm_topdir)
    #mkdir if needed
    if not os.path.isdir(new_slurm_topdir):
        os.makedirs(new_slurm_topdir, mode=0o755)
    if not os.path.isdir(new_slurm_etc):
        os.makedirs(new_slurm_etc, mode=0o755)
        
    log.info("Copying files from "+old_etc+" to "+new_slurm_etc)
    
    for f in os.listdir(old_etc):
        ffrom=os.path.join(old_etc,f)
        fto=os.path.join(new_slurm_etc,f)
        
        if overwrite and os.path.exists(fto):
            if os.path.isdir(fto):
                shutil.rmtree(fto)
            else:
                os.remove(fto)
        if os.path.isdir(ffrom):
            shutil.copytree(ffrom,fto)
        else:
            shutil.copy2(ffrom,fto)
        
    slurm_conf_loc=os.path.join(new_slurm_etc,'slurm.conf')
    slurmdbd_conf_loc=os.path.join(new_slurm_etc,'slurmdbd.conf')
    sim_conf_loc=os.path.join(new_slurm_etc,'sim.conf')
    
    def update_file(filename,vars_new_val):
        def update_line(l):
            l2=l.strip()
            l_new=l
            if len(l2)!=0 and l2[0]!='#':
                comment=l2.find('#')
                if comment>=0:
                    l2=l2[:comment]
                    l2=l2.strip()
                
                setsign=l2.find('=')
                if setsign>=0:
                    name=l2[:setsign].strip()
                    if len(l2)>setsign+1:
                        value=l2[setsign+1:].strip()
                    else:
                        value="None"
                    if name.lower() in vars_new_val:
                        l_new=name+" = "+str(vars_new_val[name.lower()])+"\n"
            return l_new
        for k in list(vars_new_val.keys()):
            vars_new_val[k.lower()]=vars_new_val[k]
        log.info("Updating "+filename)
        if not os.path.isfile(filename):
            raise Exception("Can not find "+filename)
        with open(filename,'rt') as fin:
            lines=fin.readlines()
        with open(filename,'wt') as fout:
            for l in lines:
                fout.write(update_line(l))
    
    update_file(slurm_conf_loc,{
        'JobCredentialPrivateKey':os.path.join(new_slurm_topdir, 'etc/slurm.key'),
        'JobCredentialPublicCertificate':os.path.join(new_slurm_topdir, 'etc/slurm.cert'),
        'JobCompLoc':os.path.join(new_slurm_topdir, 'log/jobcomp.log'),
        'SlurmctldLogFile':os.path.join(new_slurm_topdir, 'log/slurmctld.log'),
        'SlurmdLogFile':os.path.join(new_slurm_topdir, 'log/slurmd.log'),
        'SlurmdSpoolDir':os.path.join(new_slurm_topdir, 'var/spool'),
        'StateSaveLocation':os.path.join(new_slurm_topdir, 'var/state'),
        'SlurmSchedLogFile':os.path.join(new_slurm_topdir, 'log/slurm_sched.log'),
        'PluginDir':os.path.join(slurm_bin, 'lib/slurm'),
    })
    if os.path.isfile(slurmdbd_conf_loc):
        update_file(slurmdbd_conf_loc,{
            'PidFile':os.path.join(new_slurm_topdir, 'var/run/slurmdbd.pid'),
            'LogFile':os.path.join(new_slurm_topdir, 'log/slurmdbd.log'),
            'PluginDir':os.path.join(slurm_bin, 'lib/slurm'),
        })
    else:
        log.info("There is no slurmdb.conf")
        
    if os.path.isfile(sim_conf_loc):
        update_file(sim_conf_loc,{
            'sdiagFileOut':os.path.join(new_slurm_topdir, 'log/sdiag.out'),
            'sprioFileOut':os.path.join(new_slurm_topdir, 'log/sprio.out'),
            'sinfoFileOut':os.path.join(new_slurm_topdir, 'log/sinfo.out'),
            'squeueFileOut':os.path.join(new_slurm_topdir, 'log/squeue.out'),
            'SimStats':os.path.join(new_slurm_topdir, 'log/simstat.out')
        })
    else:
        log.info("There is no sim.conf")

if __name__ == '__main__':
    
    import argparse
        
    parser = argparse.ArgumentParser(description='''Slurm Simulator Toolkit.
    Copy Slurm etc directory to new location update pathways in slurm.conf to use new location''')
    
    parser.add_argument('-s', '--slurm-bin', required=True, type=str,
        help="top directory of slurm binaries installation")
    
    parser.add_argument('-o', '--overwrite', action='store_true', 
        help="overwrite existing files")
    
    parser.add_argument('-v', '--verbose', action='store_true', 
        help="turn on verbose logging")
    
    parser.add_argument('old_etc', type=str,
        help="etc directory for current simulation")
    parser.add_argument('new_slurm_topdir', type=str,
        help="new location of slurm topdir")
    
    args = parser.parse_args()
    
    if args.verbose:
        log.basicConfig(level=log.DEBUG,format='[%(asctime)s]-[%(levelname)s]: %(message)s')
    else:
        log.basicConfig(level=log.INFO,format='[%(asctime)s]-[%(levelname)s]: %(message)s')
    
    cp_slurm_conf_dir(args)
    