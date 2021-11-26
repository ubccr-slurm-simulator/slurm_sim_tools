#!/usr/bin/env bash
# export SLURM_HOME=/opt/slurm
# export SLURM_CONF=/opt/cluster/micro2/etc/slurm.conf
# export PATH=${SLURM_HOME}/sbin:${SLURM_HOME}/bin:${PATH}
/opt/cluster/vctools/add_system_users.sh
echo "Starting slurmd"
slurmd
