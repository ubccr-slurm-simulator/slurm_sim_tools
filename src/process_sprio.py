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

    
def process_sprio(sprio_filename,csv_filename):
    with open(sprio_filename,"rt") as fin:
        lines=fin.readlines()
    header=None
    header_len=None
    header_last_tres=None
    r=[]
    N=len(lines)
    i=0
    while i<N:
        while i<N and lines[i].count("#")<10:
            i+=1
        #time
        v=lines[i+1][3:].strip()
        vs=v.split()
        if len(vs)==6:
            v=" ".join(vs[:4])+" "+vs[5]
        t=datetime.datetime.strptime(v,'%a %b %d %H:%M:%S %Y')
        if header is None:
            header=lines[i+2].lower().split()
            header_len=len(header)
            header_last_tres=(header[-1]=="tres")
        str_t=str(t)
        i+=3
        while i<N and lines[i].count("#")<10:
            v=lines[i].split()
            
            if len(v)>1:
                if len(v)==header_len-1 and header_last_tres:
                    v.append("NA")
                if len(v)!=header_len:
                    raise Exception("Unknown line format, probably TRES can not handle it now")
                
                v.insert(1, str_t)
                r.append(v)
            i+=1
           
    header.insert(1, "t")
    print("writing output to: "+csv_filename)
    with open(csv_filename,"wt") as fout:
        fout.write(",".join(header)+"\n")
        for rr in r:
            fout.write(",".join(rr)+"\n")
    

if __name__ == '__main__':
    
    import argparse
        
    parser = argparse.ArgumentParser(description='process sdiag')
    
    parser.add_argument('-s', '--sprio', required=True, type=str,
        help="directory to process or file")
    parser.add_argument('-csv', '--csv', default="sprio.csv", type=str,
        help="name of output csv file")
    parser.add_argument('-v', '--verbose', action='store_true', 
        help="turn on verbose logging")
    
    args = parser.parse_args()
    if args.verbose:
        log.basicConfig(level=log.DEBUG,format='[%(asctime)s]-[%(levelname)s]: %(message)s')
    else:
        log.basicConfig(level=log.INFO,format='[%(asctime)s]-[%(levelname)s]: %(message)s')
    
    process_sprio(args.sprio,args.csv)
    