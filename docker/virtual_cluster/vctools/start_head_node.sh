#!/usr/bin/env bash
# export SLURM_HOME=/opt/slurm
# export SLURM_CONF=/opt/cluster/micro2/etc/slurm.conf
# export PATH=${SLURM_HOME}/sbin:${SLURM_HOME}/bin:${PATH}

echo "Dropping slurmdb_ubhpc DB"
mysql -u root << END
drop database if exists slurmdb_ubhpc;
END

/opt/cluster/vctools/add_system_users.sh

echo "Starting slurmdbd"
slurmdbd

sleep 10
echo "Running sacctmgr"
set +e
sacctmgr -i < /opt/cluster/vctools/sacctmgr.script
set -e

sleep 10
echo "Starting slurmctld"
slurmctld
ps -Af
