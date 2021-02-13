#!/usr/bin/env python3
import os
import sys
import re
from collections import OrderedDict
import pprint
import logging as log
import datetime

def process_sdiag_output(filename=None,lines=None):
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
    
    i=0
    while lines[i].count('Main schedule statistics')==0:
        if lines[i].count('sdiag output at'):
            lines[i]=lines[i].replace('sdiag output at','sdiag output time:')
        if lines[i].count('Data since    '):
            lines[i]=lines[i].replace('Data since','Data since:')
        i+=1
    
    
    
    def get_section(i,prefix,end_at):
        while i<len(lines) and lines[i].count(end_at)==0:
            f=[f.strip() for f in lines[i].strip().split(':',maxsplit=1)]
            if len(f)==2:
                v=f[0].lower().replace(' ','_').replace('(','').replace(')','')
                r[prefix+v]=f[1]
            i+=1
        return i
    
    i=1
    
    i=get_section(i,prefix='',end_at='Main schedule statistics')
    #Main schedule statistics
    i=get_section(i+1,prefix='main_schedule_statistics__',end_at='Backfilling stats')
    #Backfilling stats
    i=get_section(i+1,prefix='backfil_stats__',end_at='Remote Procedure Call statistics by message type')
    #Remote Procedure Call statistics by message type
    def get_section_rpc(i,prefix,end_at):
        while i<len(lines) and lines[i].count(end_at)==0:
            m=re.match(r"\s+(\S+)\s+\(\s*[0-9]*\)\s+count:([0-9]+)\s+ave_time:([0-9]+)\s+total_time:([0-9]+)",lines[i])
            if m!=None:
                r[prefix+m.group(1)+'__count']=m.group(2)
                r[prefix+m.group(1)+'__ave_time']=m.group(3)
                r[prefix+m.group(1)+'__total_time']=m.group(4)
            i+=1
        return i
    i=get_section_rpc(i+1,prefix='rpc_stats_by_msg_type__',end_at='Remote Procedure Call statistics by user')
    
    date_fields=[
        'sdiag_output_time',
        'data_since',
        'backfil_stats__last_cycle_when',
        'jobs_running_ts'
    ]
    for k in date_fields:
        if k not in r and k not in ['jobs_running_ts']:
            # jobs_running_ts is newer field
            print(k+" is not in "+filename)
        else:
            v=r[k]
            if v.count("(")>0:
                # it also has (epoch at the end)
                v=r[k][:r[k].index("(")].strip()
            d=datetime.datetime.strptime(v,'%a %b %d %H:%M:%S %Y')
            r[k]=str(d)
            r[k+'_ts']=int(d.timestamp())
        
    
    for k in set(r.keys())-set(date_fields):
        r[k]=int(r[k])
    
    return r

    
def process_sdiag(sdiag,csv_filename):
    r=[]
    if not os.path.exists(sdiag):
        raise Exception("path "+sdiag+" do not exists")
        
    if os.path.isdir(sdiag):
        for subdir in os.listdir(sdiag):
            subdir=os.path.join(sdiag,subdir)
            if os.path.isdir(subdir):
                for sdiag_output in sorted(os.listdir(subdir)):
                    sdiag_output=os.path.join(subdir,sdiag_output)
                    try:
                        o=process_sdiag_output(sdiag_output)
                        r.append(o)
                    except Exception as e:
                        print(e)
    elif os.path.isfile(sdiag):
        with open(sdiag,"rt") as fin:
            lines=fin.readlines()
        snapshots=[]
        for i in range(len(lines)):
            if lines[i].count("sdiag output"):
                snapshots.append(i-1)
        snapshots.append(len(lines))
        
        for i in range(len(snapshots)-1):
            #try:
                o=process_sdiag_output(lines=lines[snapshots[i]:snapshots[i+1]])
                r.append(o)
            #except Exception as e:
            #    print(e)
    else:
        raise Exception(sdiag+" is not directory nor file")
                
    #rr=dict(zip(LD[0],zip(*[d.values() for d in r])))
    #rr=OrderedDict(zip(r[0].keys(),zip(*[d.values() for d in r])))
    if len(r)==0:
        raise Exception("did not read any snapshots from "+sdiag)
    
    all_keys=list(r[0].keys())
    
    for i in range(1,len(r)):
        all_keys+=list(r[i].keys())
    
    used = set()
    all_keys=[x for x in all_keys if x not in used and (used.add(x) or True)]
    
        
    with open(csv_filename,"wt") as fout:
        fout.write(",".join(all_keys)+'\n')
        for rec in r:
            v=[]
            for k in all_keys:
                if k not in rec:
                    v.append('NA')
                else:
                    v.append(str(rec[k]))
            fout.write(",".join(v)+'\n')
    
    #print(pprint.pformat(rr,width=180))

if __name__ == '__main__':
    
    import argparse
        
    parser = argparse.ArgumentParser(description='process sdiag')
    
    parser.add_argument('-sdiag', '--sdiag', required=True, type=str,
        help="directory to process or file")
    
    parser.add_argument('-csv', '--csv', required=False, type=str, default="sdiag.csv",
        help="name of output csv file")
    parser.add_argument('-v', '--verbose', action='store_true', 
        help="turn on verbose logging")
    
    args = parser.parse_args()
    if args.verbose:
        log.basicConfig(level=log.DEBUG,format='[%(asctime)s]-[%(levelname)s]: %(message)s')
    else:
        log.basicConfig(level=log.INFO,format='[%(asctime)s]-[%(levelname)s]: %(message)s')
    
    process_sdiag(args.sdiag,args.csv)
    