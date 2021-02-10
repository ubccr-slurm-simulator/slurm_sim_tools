#!/usr/bin/env python3

#This python script sets up the micro Cluster simulation to run by calling other scripts

# using these to work with calling files to do things
import os
import subprocess

from time import sleep,time # need sleep to do the sleep(3) after dbd


# this function starts a process and then waits for it to finish before being done
def start_finish_process(file_path):
	proc = subprocess.Popen(args=file_path)
	proc.wait() # wait for process to finish
	print("Finished process of: " + file_path)
	return proc


# function to start up the slurmdbd
def startup_slurmdbd(dbd_loc, conf_loc):
	proc = subprocess.Popen(args=[dbd_loc, "-Dvvv"], env={"SLURM_CONF": conf_loc} ) # runs the dbd in environment with the SLURM_CONF variable set
	sleep(3) # sleeps to allow for spin up time
	print("Started up the Slurmdbd")
	return proc


# function that just prints out what processes are going on (helpful for seeing whats going on)
def check_processes():
	checkPs = subprocess.Popen(args="ps -A", shell=True)
	checkPs.wait()
	return


# goes through the process list and kills all the processes
def kill_processes(proc_list):
	for p in proc_list:
		if p!=None:
			p.kill()
			p=None
			

# main "function"
if __name__ == "__main__":
	
	process_list = [] # starts a list of processes (each process is added to it)


	#microcluster workspace and slurm configuration setup
	setup_ws_config_proc = start_finish_process("/install_files/micro_ws_config.sh") 
	process_list.append(setup_ws_config_proc)
	
	# the two parts of starting slurm dbd in "foreground" mode
	slurmdbd_loc = "/home/slurm/slurm_sim_ws/slurm_opt/sbin/slurmdbd"
	slurm_conf_loc = "/home/slurm/slurm_sim_ws/sim/micro/baseline/etc/slurm.conf"
	
	# process to start up the slurmdbd
	slurmdbd_proc = startup_slurmdbd(slurmdbd_loc, slurm_conf_loc)
	process_list.append(slurmdbd_proc)
	
	# prints processes going on
	check_processes()
	
	# process to populate the slurmdb
	pop_slurmdb_proc = start_finish_process("/install_files/populate_slurmdb.sh")
	process_list.append(pop_slurmdb_proc)
	
	check_processes()
	
	# kills all the processes in the list (don't need them)
	kill_processes(process_list)
	
	# calls file that generates all the test jobs for the test simulation	
	gen_jobs_proc = start_finish_process("/install_files/generate_job_trace.sh")

	# Done setting up the micro cluster sim - ready to run it



