#!/bin/bash

slurm_dir=/home/mikola/slurm_simulator3/slurm_real

sdiag=${slurm_dir}/bin/sdiag
squeue=${slurm_dir}/bin/squeue
sinfo=${slurm_dir}/bin/sinfo
sprio=${slurm_dir}/bin/sprio

out_dir=./
sdiag_out=${out_dir}/sdiag.out
squeue_out=${out_dir}/squeue.out
sinfo_out=${out_dir}/sinfo.out
sprio_out=${out_dir}/sprio.out

sep="###############################################################################"

for f in $sdiag_out $squeue_out $sinfo_out $sprio_out
do
	if [ -e "$f" ]
	then
		rm $f
	fi
done

while true
do
	#sdiag
	$sdiag >> $sdiag_out
	#squeue
	echo $sep >> $squeue_out
	echo "t: "`date` >> $squeue_out
	$squeue >> $squeue_out
	#sinfo
	echo $sep >> $sinfo_out
	echo "t: "`date` >> $sinfo_out
	$sinfo >> $sinfo_out
	#sprio
	echo $sep >> $sprio_out
	echo "t: "`date` >> $sprio_out
	$sprio >> $sprio_out
	
	date
	
	current_epoch=$(date +%s)
	((sleep_seconds=($current_epoch/60)*60+60-$current_epoch))
	sleep $sleep_seconds
done
