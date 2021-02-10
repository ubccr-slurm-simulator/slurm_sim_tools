#!/bin/bash

mkdir -p ~/results/jobs500

for dtstart in 10 30 50 70 90 110
do
    for i in {1..4}
    do
        sudo /opt/slurm_sim_tools/src/run_slurm.py -s /opt/slurm_front_end -e /opt/cluster/micro1/etc \
            -t /opt/cluster/micro1/etc/jobs500.events \
            -r ~/results/jobs500/dtstart_${dtstart}_${i} -a /opt/cluster/micro1/etc/sacctmgr.sh \
            -d -v -dtstart ${dtstart} &> ~/results/jobs500/jobs500_dtstart_${dtstart}_${i}.log
    done
done
