#!/usr/bin/env python3
import os
import sys
import re
from collections import OrderedDict
import pprint
import logging as log
import datetime
import pandas as pd
import traceback

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

    
def process_squeue(squeue,cluster,csv_filename):
    r=[]
    if os.path.isdir(squeue):
        for subdir in os.listdir(squeue):
            t0=subdir
            subdir=os.path.join(squeue,subdir)
            if os.path.isdir(subdir):
                for soutput in sorted(os.listdir(subdir)):
                    t=t0+" "+soutput.replace(".txt","")
                    soutput=os.path.join(subdir,soutput)
                    try:
                        d=datetime.datetime.strptime(t,'%Y-%m-%d %H-%M-%S')
                        o=process_squeue_output(cluster,soutput)
                        r.append((d,o))
                    except Exception as e:
                        print(soutput)
                        print(e)
                        traceback.print_exc()
            #break
    elif os.path.isfile(squeue):
        with open(squeue,"rt") as fin:
            lines=fin.readlines()
        snapshots=[]
        for i in range(len(lines)):
            if lines[i].count("squeue output time"):
                snapshots.append(i-1)
        snapshots.append(len(lines))
        
        for i in range(len(snapshots)-1):
            #try:
                o=process_squeue_output(cluster,lines=lines[snapshots[i]:snapshots[i+1]])
                r.append(o)
            #except Exception as e:
            #    print(e)
    else:
        raise Exception(squeue+" is not directory nor file")
                
    #rr=dict(zip(LD[0],zip(*[d.values() for d in r])))
    #rr=OrderedDict(zip(r[0].keys(),zip(*[d.values() for d in r])))
    #print(r)
    
    
    all_keys=set()
    for i in range(0,len(r)):
        for k in list(r[i][1].keys()):
            all_keys.add(k)
    
    with open(csv_filename,"wt") as fout:
        fout.write("datetime,"+(",".join(all_keys))+'\n')
        for t,rec in r:
            v=[str(t)]
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
    
    parser.add_argument('-s', '--squeue', required=True, type=str,
        help="directory to process or file")
    parser.add_argument('-c', '--cluster', required=True, type=str,
        help="cluster")
    parser.add_argument('-csv', '--csv', default="squeue.csv", type=str,
        help="name of output csv file")
    parser.add_argument('-v', '--verbose', action='store_true', 
        help="turn on verbose logging")
    
    args = parser.parse_args()
    if args.verbose:
        log.basicConfig(level=log.DEBUG,format='[%(asctime)s]-[%(levelname)s]: %(message)s')
    else:
        log.basicConfig(level=log.INFO,format='[%(asctime)s]-[%(levelname)s]: %(message)s')
    
    process_squeue(args.squeue,args.cluster,args.csv)
    