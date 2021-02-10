# Documentation on Development

```
/home/slurm                       - Slurm user home derectory
      └── slurm_sim_ws            - Slurm simulator work space
          ├── bld                 - Slurm building directory
          │   ├── slurm_sim_deb   - Debug version building
          │   └── slurm_sim_opt   - Optimized version building
          ├── sim                 - Directory where simulation will be performed
          │   └── <system name>   - Directory where simulation of particular system will be performed
          │       └── <conf name> - Directory where simulation of particular configuration will be performed
          │           ├── etc     - Directory with configuration
          │           ├── log     - Directory with logs
          │           └── var     - Directory varius slurm output
          ├── slurm_sim_opt       - Slurm simulator binary installation directory
          ├── slurm_sim_deb       - Slurm simulator debug binary installation directory
          ├── slurm_sim_tools     - Slurm simulator toolkit
          └── slurm_simulator     - Slurm simulator source code
```

# Building

```bash
[[ -d "$HOME/slurm_sim_ws/slurm_sim_deb" ]] && rm -rf $HOME/slurm_sim_ws/slurm_sim_deb
$HOME/slurm_sim_ws/slurm_simulator/configure --prefix=$HOME/slurm_sim_ws/slurm_sim_deb \
    --enable-developer --disable-optimizations --enable-debug --disable-x11 --enable-front-end \
    --with-hdf5=no CFLAGS="-g -O0"
make -j
make install
```

# MySQL Set-up

```mysql
create user 'slurm'@'localhost' identified by 'slurm';
grant all privileges on *.* to 'slurm'@'localhost' with grant option;
```

This way slurmdbd can create all required tables

# Test Cluster

```bash
#set some vars
export SLURM_SIM_WS=$HOME/slurm_sim_ws
export SLURM_WORKDIR=$SLURM_SIM_WS/sim/micro1/test
export SLURM_DIR=$SLURM_SIM_WS/slurm_sim_deb
export SLURM_CONF=$SLURM_WORKDIR/etc/slurm.conf
export PATH=$SLURM_DIR/bin:$SLURM_DIR/sbin:$PATH

# copy 
mkdir -p $SLURM_WORKDIR/bin
mkdir -p $SLURM_WORKDIR/etc
mkdir -p $SLURM_WORKDIR/log
mkdir -p $SLURM_WORKDIR/var/spool
mkdir -p SLURM_WORKDIR/var/state

cp -r $SLURM_SIM_WS/slurm_sim_tools/developing/micro1/bin/* $SLURM_WORKDIR/bin
cp -r $SLURM_SIM_WS/slurm_sim_tools/developing/micro1/etc/* $SLURM_WORKDIR/etc

cd $SLURM_WORKDIR
sed -i "s|SLURM_WORKDIR|$SLURM_WORKDIR|g" ./etc/*.conf
sed -i "s|SLURM_DIR|$SLURM_DIR|g" ./etc/*.conf
sed -i "s|SLURM_USER|$USER|g" ./etc/*.conf
sed -i "s|=SLURM_DIR|=$SLURM_DIR|g" ./bin/env.sh

```

# Populate SlurmDB

Start slurmdbd in foreground mode:
```bash
slurmdbd -Dvvvv
# or
$SLURM_WORKDIR/bin/start_slurmdbd.sh
```

In separate terminal populate SlurmDB using Slurm _sacctmgr_ utility:
```bash

# add QOS
sacctmgr  -i modify QOS set normal Priority=0
sacctmgr  -i add QOS Name=supporters Priority=100
# add cluster
sacctmgr -i add cluster Name=micro1 Fairshare=1 QOS=normal,supporters
# add accounts
sacctmgr -i add account name=account0 Fairshare=100
sacctmgr -i add account name=account1 Fairshare=100
sacctmgr -i add account name=account2 Fairshare=100
#sacctmgr -i add user name=mikola DefaultAccount=account0 MaxSubmitJobs=1000 AdminLevel=Administrator
# add users
sacctmgr -i add user name=$USER DefaultAccount=account0 MaxSubmitJobs=1000
sacctmgr -i add user name=user1 DefaultAccount=account1 MaxSubmitJobs=1000
sacctmgr -i add user name=user2 DefaultAccount=account1 MaxSubmitJobs=1000
sacctmgr -i add user name=user3 DefaultAccount=account1 MaxSubmitJobs=1000
sacctmgr -i add user name=user4 DefaultAccount=account2 MaxSubmitJobs=1000
sacctmgr -i add user name=user5 DefaultAccount=account2 MaxSubmitJobs=1000 

sacctmgr -i modify user set qoslevel="normal,supporters"

```

# Start SlurmCtrl
```bash
slurmctld -Dvvvv
```

Start slurmdbd in foreground mode:


SlurmD should run as root
```bash
sudo $SLURM_WORKDIR/bin/start_slurmdbd.sh
```

# Test Cluster

```bash
#set some vars
export SLURM_SIM_WS=$HOME/slurm_sim_ws
export SLURM_WORKDIR=$SLURM_SIM_WS/sim/micro1/test
export SLURM_DIR=$SLURM_SIM_WS/slurm_sim_deb
export SLURM_CONF=$SLURM_WORKDIR/etc/slurm.conf
export PATH=$SLURM_DIR/bin:$SLURM_DIR/sbin:$PATH

```

## Starting Unmodified Slurm

```bash
slurmdbd -Dvvvv
slurmctld -Dvvvv
slurmd -Dvvvv
sbatch -t 1:00 -n 1 -A account0 -p normal -q normal /home/nikolays/slurm_sim_ws/slurm_sim_tools/miniapp/sleep.job 1200 0
```

> **Time format for wall duration:**
> A time limit of zero requests that no time limit  be  imposed.   
> Acceptable  time  formats  include  "minutes",  "minutes:seconds",  
> "hours:minutes:seconds",  "days-hours", "days-hours:minutes" and "days-hours:minutes:seconds"

# Slurm Communications

## Slurmd registration

```
During initiation of slurmd
slurmd: do send_registration_msg(SLURM_SUCCESS, true)

slurmctld: debug2: Processing RPC: MESSAGE_NODE_REGISTRATION_STATUS from uid=1000
slurmctld: debug2: name:localhost boot_time:1602515022 up_time:2768574
slurmctld: debug:  Nodes b1,m[1-4],n[1-4] have registered
slurmctld: debug2: _slurm_rpc_node_registration complete for localhost usec=411

After that nodes are marked as UP
```

## Job 

```
slurmctld: debug2: Processing RPC: REQUEST_SUBMIT_BATCH_JOB from uid=1000
# Job Start
slurmctld: debug2: Spawning RPC agent for msg_type REQUEST_BATCH_JOB_LAUNCH
slurmd: debug2: Start processing RPC: REQUEST_BATCH_JOB_LAUNCH
slurmd: debug2: Processing RPC: REQUEST_BATCH_JOB_LAUNCH

# Job end due to exceeding of timelimit
slurmctld: debug2: Spawning RPC agent for msg_type REQUEST_KILL_TIMELIMIT
slurmd: debug2: Start processing RPC: REQUEST_KILL_TIMELIMIT
slurmd: debug2: Processing RPC: REQUEST_KILL_TIMELIMIT
slurmd: debug2: Finish processing RPC: REQUEST_KILL_TIMELIMIT

slurmctld: debug2: Processing RPC: REQUEST_COMPLETE_BATCH_SCRIPT from uid=1000 JobId=1001
slurmctld: debug2: _slurm_rpc_complete_batch_script JobId=1001: Job/step already completing or completed 
slurmctld: debug2: Processing RPC: MESSAGE_EPILOG_COMPLETE uid=1000
slurmctld: debug2: _slurm_rpc_epilog_complete: JobId=1001 Node=localhost 

# Job end due to job compleation
slurmctld: debug2: Processing RPC: REQUEST_COMPLETE_BATCH_SCRIPT from uid=1000 JobId=1002
slurmctld: _job_complete: JobId=1002 WEXITSTATUS 0
slurmctld: error: slurm_jobcomp plugin context not initialized
slurmctld: debug3: select/cons_res: job_res_rm_job: JobId=1002 action 0
slurmctld: debug3: select/cons_res: job_res_rm_job: removed JobId=1002 from part normal row 0
slurmctld: _job_complete: JobId=1002 done
slurmctld: debug2: _slurm_rpc_complete_batch_script JobId=1002 usec=531
slurmctld: debug2: Spawning RPC agent for msg_type REQUEST_TERMINATE_JOB

slurmd: debug2: Finish processing RPC: REQUEST_BATCH_JOB_LAUNCH
slurmd: debug3: in the service_connection
slurmd: debug2: Start processing RPC: REQUEST_TERMINATE_JOB
slurmd: debug2: Processing RPC: REQUEST_TERMINATE_JOB
slurmd: debug:  _rpc_terminate_job, uid = 1000
slurmd: debug:  task_p_slurmd_release_resources: 1002
slurmd: debug3: state for jobid 1002: ctime:1602516021 revoked:0 expires:2147483647
slurmd: debug:  credential for job 1002 revoked
slurmd: debug2: No steps in jobid 1002 to send signal 18
slurmd: debug2: No steps in jobid 1002 to send signal 15
slurmd: debug4: sent ALREADY_COMPLETE
slurmd: debug2: set revoke expiration for jobid 1002 to 1602516171 UTS
slurmd: debug2: Finish processing RPC: REQUEST_TERMINATE_JOB
```



```bash
module load slurm/sim_deb vc/micro1_test
cd $SLURM_WORKDIR

slurmdbd -Dvvvv
slurmctld -Dvvvv


rm -rf core slurm-*.out sched.log slurmctld.pid SLURM_WORKDIR log/* var/spool/* var/state/*;slurmctld -Dvvvv

```


# Notes on Running Slurm in Front End mode to generate refference data

Set `SlurmdParameters=config_overrides` in slurm.conf to assume configuration for gres from config.

source /etc/pcp.conf
$PCP_RC_DIR/pcp start

