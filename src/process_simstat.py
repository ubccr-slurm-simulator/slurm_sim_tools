#!/usr/bin/env python3
import os
import sys
import re
from collections import OrderedDict
import pprint
import logging as log
import datetime

def process_simstat_output(filename=None,lines=None):
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
    
    i=1
    while i<len(lines):
        f=[f.strip() for f in lines[i].strip().split(':',maxsplit=1)]
        if len(f)==2:
            v=f[0].lower().replace(' ','_').replace('(','').replace(')','')
            r[v]=f[1]
        i+=1
        
    date_fields=[
        'output_time','last_cycle_when'
    ]
    for k in date_fields:
        if k not in r:
            print(k+" is not in "+filename)
        else:
            d=datetime.datetime.strptime(r[k],'%a %b %d %H:%M:%S %Y')
            r[k]=str(d)
            r[k+'_ts']=int(d.timestamp())
        
    
    for k in set(r.keys())-set(date_fields)-set(['']):
        if str(r[k]).count('.'):
            r[k]=float(r[k])
        else:
            r[k]=int(r[k])
    return r

    
def process_simstat(simstat,csv_filename):
    r=[]

    with open(simstat,"rt") as fin:
        lines=fin.readlines()
    snapshots=[]
    for i in range(len(lines)):
        if lines[i].count("**************************************"):
            snapshots.append(i)
    snapshots.append(len(lines))
    
    for i in range(len(snapshots)-1):
        #try:
        if lines[snapshots[i]].count("*Backfill*Stats*")>0:
            o=process_simstat_output(lines=lines[snapshots[i]:snapshots[i+1]])
            r.append(o)
        #except Exception as e:
        #    print(e)
    

                
    #rr=dict(zip(LD[0],zip(*[d.values() for d in r])))
    #rr=OrderedDict(zip(r[0].keys(),zip(*[d.values() for d in r])))
    
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
        
    parser = argparse.ArgumentParser(description='process simstat')
    
    parser.add_argument('-s', '--simstat', required=True, type=str,
        help="directory to process or file")
    
    parser.add_argument('-bcsv', '--bcsv', required=False, type=str, default="simstat_backfill.csv",
        help="name of output csv file")
    parser.add_argument('-v', '--verbose', action='store_true', 
        help="turn on verbose logging")
    
    args = parser.parse_args()
    if args.verbose:
        log.basicConfig(level=log.DEBUG,format='[%(asctime)s]-[%(levelname)s]: %(message)s')
    else:
        log.basicConfig(level=log.INFO,format='[%(asctime)s]-[%(levelname)s]: %(message)s')
    
    process_simstat(args.simstat,args.bcsv)
    