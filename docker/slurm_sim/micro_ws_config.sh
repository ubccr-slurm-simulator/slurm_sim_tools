#!/bin/bash

# This script sets up the workspace and slurm configuration for the micro cluster simulation

echo "Starting micro cluster sim ws and slurm configuration...."

# initiating workspace for micro-cluster simulation
cd /home/slurm/slurm_sim_ws
mkdir -p /home/slurm/slurm_sim_ws/sim/micro

# creating slurm configuration properly
cd /home/slurm/slurm_sim_ws
/home/slurm/slurm_sim_ws/slurm_sim_tools/src/cp_slurm_conf_dir.py -o -s /home/slurm/slurm_sim_ws/slurm_opt /home/slurm/slurm_sim_ws/slurm_sim_tools/reg_testing/micro_cluster/etc /home/slurm/slurm_sim_ws/sim/micro/baseline

echo "Finished with workspace setup and configuration"









