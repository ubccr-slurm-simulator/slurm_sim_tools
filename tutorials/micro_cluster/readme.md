Slurm Simulator: Micro Cluster Tutorial
================
<nikolays@buffalo.edu>
30 May, 2024

- [Slurm Simulator: Micro Cluster
  Tutorial](#slurm-simulator-micro-cluster-tutorial)
  - [Overview](#overview)
  - [Micro-Cluster Description](#micro-cluster-description)
  - [Slurm Simulation Configuration](#slurm-simulation-configuration)
    - [Adopting the Slurm Configuration for
      Simulation](#adopting-the-slurm-configuration-for-simulation)
      - [Changes in `slurm.conf`](#changes-in-slurmconf)
      - [Changes in `slurmdbd.conf`](#changes-in-slurmdbdconf)
      - [Changes to `gres.conf`](#changes-to-gresconf)
      - [Changes to `topology.conf`](#changes-to-topologyconf)
    - [Set up Users, Accounts, QoS
      Specs](#set-up-users-accounts-qos-specs)
      - [System User names and Groups -
        `users.sim`](#system-user-names-and-groups---userssim)
      - [Adding Users, Accounts and QoS -
        `sacctmgr.script`](#adding-users-accounts-and-qos---sacctmgrscript)
  - [Simulation Parameters](#simulation-parameters)
  - [Workload Specification (events file, a.k.a. job
    traces)](#workload-specification-events-file-aka-job-traces)
  - [Run First Simulations](#run-first-simulations)
  - [Read Results](#read-results)
  - [Make Events Plot](#make-events-plot)
- [Run and Analyse Multiple Independent
  Simulations](#run-and-analyse-multiple-independent-simulations)
  - [Generate Random Start Times
    Delay](#generate-random-start-times-delay)
  - [Run the Similations](#run-the-similations)
  - [Read Results](#read-results-1)
  - [Analyse the Results](#analyse-the-results)

# Slurm Simulator: Micro Cluster Tutorial

``` bash
# Check that MySQL Server is up
ps -Af | grep mariadbd 
```

    ## mysql      151    23  0 May29 pts/0    00:00:13 /usr/sbin/mariadbd --basedir=/usr --datadir=/var/lib/mysql --plugin-dir=/usr/lib/mysql/plugin --user=mysql --skip-log-error --pid-file=/run/mysqld/mysqld.pid --socket=/run/mysqld/mysqld.sock
    ## slurm    40241 38929  0 19:17 ?        00:00:00 sh -c 'bash'  -c '# Check that MySQL Server is up ps -Af | grep mariadbd ' 2>&1
    ## slurm    40242 40241  0 19:17 ?        00:00:00 bash -c # Check that MySQL Server is up ps -Af | grep mariadbd 
    ## slurm    40244 40242  0 19:17 ?        00:00:00 grep mariadbd

## Overview

This tutorial will teach you how to run a Slurm Simulator using an
example of a small 10-node Micro-Cluster.

The tutorial will walk you through the Slurm simulation configuration.

You will run two simulations with identical workloads but different
timing between the start-up and first job to investigate scheduling
stochasticity.

Finally, you’ll run ten independent simulations with the same workload
and calculate statistics other than runs.

The files needed for this tutorial are located at
`slurm_sim_tools/tutorials/micro_cluster`.

## Micro-Cluster Description

In this tutorial small model cluster, named Micro-Cluster, will be
simulated. Micro-Cluster is created to test various aspects of the slurm
simulator usage. It consists of 10 compute nodes (see Table below).
There are two types of general compute nodes with different CPU types to
test features request (constrains), one GPU node to test GRes and one
big memory node to test proper allocation of jobs with large memory
requests.

| Node Type       | Node Name | Number of Cores | CPU Type | Memory Size | Number of GPUs |
|-----------------|-----------|-----------------|----------|-------------|----------------|
| General Compute | n\[1-4\]  | 12              | CPU-N    | 48GiB       | \-             |
| General Compute | m\[1-4\]  | 12              | CPU-M    | 48GiB       | \-             |
| GPU node        | g1        | 12              | CPU-G    | 48GiB       | 2              |
| Big memory      | b1        | 12              | CPU-G    | 512GiB      | \-             |

Micro-Cluster compute nodes description

The nodes are connected as follows:

    Top Switch
     ├─IBN Switch
     │  ├─Node n1
     │  ├─Node n2
     │  ├─Node n3
     │  └─Node n4
     ├─IBM Switch
     │  ├─Node m1
     │  ├─Node m2
     │  ├─Node m3
     │  └─Node m4
     └─IBG Switch
        ├─Node g1
       `└─Node b1

## Slurm Simulation Configuration

The UB Slurm Simulator is made from Slurm source code and so it shares
many configurations with actual Slurm installation. In addition, you
also need to specify that simulated users will submit to the simulated
cluster and some simulation parameters.

In order to run Slurm simulation you need:

1.  Adopt the Slurm configuration (`slurm.conf` and friends) for
    simulation
    - Some options are not supported and files, typically used in slurm
      need to be renamed and point to user space.
2.  Set-up users and accounts: create `sacctmgr.script` and `user.sim`.
3.  Specify simulation parameters
    - `sim.conf` some of parameters needed to be reset at run-time
4.  Create events file with workload specification (a.k.a. job-traces or
    events-list).

``` bash
ls etc
```

    ## gres.conf
    ## sacctmgr.script
    ## sim.conf
    ## slurm.cert
    ## slurm.conf
    ## slurmdbd.conf
    ## slurm.key
    ## topology.conf
    ## users.sim

### Adopting the Slurm Configuration for Simulation

The simulator is built from Slurm code and uses regular Slurm
configuration.

In the `etc` directory, you can find several familiar Slurm
configuration files: `slurm.conf`, `topology.conf`, `gres.conf` and
`slurmdbd.conf`.

When you start from the actual cluster configuration, some modifications
are needed to point to different file system locations and disable some
features which the simulator cannot work with.

The files in this tutorial are already modified to be executed in
simulator mode. In the following sub-section, we will list those
changes.

#### Changes in `slurm.conf`

``` ini
# (optional) Different cluster name might be useful
ClusterName=micro

# Authentication is turned off
AuthType=auth/none

# This user will be used to run slurm simulator
SlurmUser=slurm
# (not needed) UB Slurm simulator does not use slurmd
SlurmdUser=root
# (not needed) This parameter is for Virtual Clusters (not used in Simulator)
SlurmdParameters=config_overrides

# Change Slurm control daemon address to localhost
ControlMachine=localhost
ControlAddr=localhost
# Change Slurm Database daemon address to localhost
AccountingStorageHost=localhost

# Change file location
JobCredentialPrivateKey=/home/slurm/work/micro_cluster/etc/slurm.key
JobCredentialPublicCertificate=/home/slurm/work/micro_cluster/etc/slurm.cert
SlurmSchedLogFile=/home/slurm/work/micro_cluster/log/sched.log
SlurmctldLogFile=/home/slurm/work/micro_cluster/log/slurmctld.log
SlurmdLogFile=/home/slurm/work/micro_cluster/log/slurmd.log
SlurmdSpoolDir=/home/slurm/work/micro_cluster/var/spool
StateSaveLocation=/home/slurm/work/micro_cluster/var/state
JobCompLoc=/home/slurm/work/micro_cluster/log/jobcomp.log

# Have to set it as simulator uses front-end mode
FrontEndName=localhost
```

#### Changes in `slurmdbd.conf`

``` ini
# Change Slurm Database daemon address to localhost
DbdHost=localhost
# Authentication is turned off
AuthType=auth/none

# Change file location
PidFile=/home/slurm/work/micro_cluster/var/slurmdbd.pid
LogFile=/home/slurm/work/micro_cluster/log/slurmdbd.log

# Change mysql server address to localhost and accounts
StorageHost=localhost
StorageUser=slurm
StoragePass=slurm
# This user will be used to run slurm dbd
SlurmUser=jovyan
# (optional) database name in mysql to use
StorageLoc=slurmdb_micro
```

#### Changes to `gres.conf`

``` ini
# There is no actual hardware everything should be specified manually
AutoDetect=off
```

#### Changes to `topology.conf`

It should be fine as is.

### Set up Users, Accounts, QoS Specs

Usually system administrator will create user and accounts on the HPC
resource on per need base. In simulator, we need to create a file with
simulated system usernames and a script for Slurm `sacctmgr` utility to
initiate cluster QoS-es, users and accounts.

#### System User names and Groups - `users.sim`

`users.sim` fount in `etc` folder specify simulated system users and
group names and ids. The file format is one line per user with colon
(`:`) separated four fields:

    <user named>:<user id>:<group name>:<group id>

The used `users.sim` file is as follows:

    admin:1000:admin:1000
    user1:1001:group1:1001
    user2:1002:group2:1002
    user3:1003:group3:1003
    user4:1004:group2:1002
    user5:1005:group1:1001

#### Adding Users, Accounts and QoS - `sacctmgr.script`

`sacctmgr.script` is a script which will be executed by `sacctmgr`
before the simulation. It adds slurm users, accounts, QoS and all other
things sys-admins will do with sacctmgr.

Below is a listing of used `sacctmgr.script`:

``` shell
# add/modify QOS
modify QOS set normal Priority=0
add QOS Name=supporters Priority=100
# add cluster
add cluster Name=micro Fairshare=1 QOS=normal,supporters
# add accounts
add account name=account0 Fairshare=100
add account name=account1 Fairshare=100
add account name=account2 Fairshare=100
# add admin
add user name=admin DefaultAccount=account0 MaxSubmitJobs=1000 AdminLevel=Administrator
# add users
add user name=user1 DefaultAccount=account1 MaxSubmitJobs=1000
add user name=user2 DefaultAccount=account1 MaxSubmitJobs=1000
add user name=user3 DefaultAccount=account1 MaxSubmitJobs=1000
add user name=user4 DefaultAccount=account2 MaxSubmitJobs=1000
add user name=user5 DefaultAccount=account2 MaxSubmitJobs=1000
# add users to qos level
modify user set qoslevel="normal,supporters"

# check results
list associations format=Account,Cluster,User,Fairshare tree withd
```

The script starts with modification of `normal` QoS and adding new QoS,
`priority`, with higher priority factor.

Then, we add Slurm users and accounts. Slurm user names should match the
system user names we specified at `users.sim`.

Here we have 5 users (user1, user2, user3, user4, user5) grouped into 2
accounts (account1, account2). There is also an admin user with an
associated account. We allowed all users to use both QoS-es.

Finally, we printed created association (relationship between users and
accounts)

## Simulation Parameters

In the etc directory, you can find several configuration files:

``` ini
# Simulation Configuration

## Unix time stamp for the simulated start time
TimeStart = 1641013200.0
## Unix time stamp for the simulated stop time, 0 - run till all jobs are finished
TimeStop = 0
## Time between simulator start and first job execution (can be overwritten by `slurmsim run_sim`)
SecondsBeforeFirstJob = 126
## CPU clock scaling
ClockScaling = 1.0
## Events File (can be overwritten by `slurmsim run_sim`)
EventsFile = /home/slurm/work/micro_cluster/job_traces/jobs500_shrinked.events
## Seconds after all events are done, -1 keep spinning time_after_all_events_done.
TimeAfterAllEventsDone = 10

## Some time delays to mimic start-up times of actual Slurm controller
FirstJobDelay = -0.32
CompJobDelay = 0.000
TimeLimitDelay = 0.000
```

Some of these parameters can be overwritten from the command line

## Workload Specification (events file, a.k.a. job traces)

In `job_traces` you can find many files finished with `.events`
extension, these are events list file which used to specify users
activities on simulated cluster.

Here is the listing of `small.events`:

``` bash
-dt 0 -e submit_batch_job | -J jobid_1001 -sim-walltime 0 --uid=user5 -t 00:01:00 -n 12 --ntasks-per-node=12 -A account2 -p normal -q normal pseudo.job
-dt 1 -e submit_batch_job | -J jobid_1002 -sim-walltime -1 --uid=user1 -t 00:01:00 -n 1 --ntasks-per-node=1 -A account1 -p normal -q normal --constraint=CPU-N pseudo.job
-dt 2 -e submit_batch_job | -J jobid_1003 -sim-walltime 5 --uid=user4 -t 00:01:00 -n 1 --ntasks-per-node=1 -A account2 -p normal -q normal --mem=500000 pseudo.job
-dt 16 -e submit_batch_job | -J jobid_1004 -sim-walltime 21 --uid=user3 -t 00:01:00 -n 24 --ntasks-per-node=12 -A account1 -p normal -q normal pseudo.job
-dt 19 -e submit_batch_job | -J jobid_1005 -sim-walltime 2 --uid=user5 -t 00:01:00 -n 12 --ntasks-per-node=12 -A account2 -p normal -q normal --mem=500000 pseudo.job
-dt 19 -e submit_batch_job | -J jobid_1006 -sim-walltime 9 --uid=user3 -t 00:01:00 -n 48 --ntasks-per-node=12 -A account1 -p normal -q normal pseudo.job
-dt 19 -e submit_batch_job | -J jobid_1007 -sim-walltime -1 --uid=user4 -t 00:01:00 -n 24 --ntasks-per-node=12 -A account2 -p normal -q normal --constraint=CPU-M pseudo.job
-dt 22 -e submit_batch_job | -J jobid_1008 -sim-walltime 0 --uid=user4 -t 00:01:00 -n 12 --ntasks-per-node=12 -A account2 -p normal -q normal --constraint=CPU-M pseudo.job
-dt 26 -e submit_batch_job | -J jobid_1009 -sim-walltime 2 --uid=user1 -t 00:01:00 -n 96 --ntasks-per-node=12 -A account1 -p normal -q normal pseudo.job
-dt 26 -e submit_batch_job | -J jobid_1010 -sim-walltime 0 --uid=user5 -t 00:01:00 -n 12 --ntasks-per-node=12 -A account2 -p normal -q normal --constraint=CPU-N pseudo.job
-dt 29 -e submit_batch_job | -J jobid_1011 -sim-walltime 0 --uid=user4 -t 00:01:00 -n 1 --ntasks-per-node=1 -A account2 -p normal -q normal --gres=gpu:1 pseudo.job
-dt 32 -e submit_batch_job | -J jobid_1012 -sim-walltime -1 --uid=user5 -t 00:01:00 -n 1 --ntasks-per-node=1 -A account2 -p normal -q normal pseudo.job
-dt 36 -e submit_batch_job | -J jobid_1013 -sim-walltime 0 --uid=user2 -t 00:01:00 -n 1 --ntasks-per-node=1 -A account1 -p normal -q normal --mem=500000 pseudo.job
-dt 36 -e submit_batch_job | -J jobid_1014 -sim-walltime 7 --uid=user5 -t 00:01:00 -n 24 --ntasks-per-node=12 -A account2 -p normal -q normal --constraint=CPU-N pseudo.job
-dt 39 -e submit_batch_job | -J jobid_1015 -sim-walltime 18 --uid=user2 -t 00:01:00 -n 6 --ntasks-per-node=6 -A account1 -p normal -q normal pseudo.job
-dt 40 -e submit_batch_job | -J jobid_1016 -sim-walltime 25 --uid=user1 -t 00:01:00 -n 2 --ntasks-per-node=2 -A account1 -p normal -q normal --gres=gpu:2 pseudo.job
-dt 42 -e submit_batch_job | -J jobid_1017 -sim-walltime 1 --uid=user1 -t 00:01:00 -n 48 --ntasks-per-node=12 -A account1 -p normal -q normal --constraint=CPU-N pseudo.job
-dt 42 -e submit_batch_job | -J jobid_1018 -sim-walltime 0 --uid=user3 -t 00:01:00 -n 12 --ntasks-per-node=12 -A account1 -p normal -q normal pseudo.job
-dt 43 -e submit_batch_job | -J jobid_1019 -sim-walltime 34 --uid=user4 -t 00:01:00 -n 12 --ntasks-per-node=12 -A account2 -p normal -q normal --gres=gpu:2 pseudo.job
-dt 43 -e submit_batch_job | -J jobid_1020 -sim-walltime 14 --uid=user1 -t 00:01:00 -n 1 --ntasks-per-node=1 -A account1 -p normal -q normal --constraint=CPU-N pseudo.job
```

Each line corresponds to a single event, the arguments till the first
pipe symbol (`|`) correspond to event time and event type, and arguments
after the pipe symbol (`|`) correspond to event parameters. For the
user’s job submission format, the arguments are just like you submit to
the `sbatch` command (it is processed by the same function), there are
some additional arguments and some normal `sbatch` arguments which have
to follow certain format. Bellow is the format:

    -dt <time to submit since the start of slurm controller> -e submit_batch_job | -J jobid_<jobid> -sim-walltime <walltime in seconds> --uid=<user> -t <requested time> -A <account> <Other Normal Slurm Arguments> pseudo.job

Here is a list of some often used `sbatch` arguments and
simulator-augmented

- `-J jobid_<jobid>`: `-J` is a normal Slurm argument to specify
  jobname, we use it for results processing automation, so give all jobs
  names like `jobid_<jobid>`, where `<jobid>` is numeric job-id.
  Some-times your simulation can be misconfigured and automatically
  assigned numeric `job-id` can be misalligned.
- `-sim-walltime <walltime in seconds>`: specify walltime for job to
  run. Value `0` means job have to be killed by Slurm due to running
  outside of time-limit.
- `--uid=<user>`: it is a normal Slurm argument but we is it to specify
  which user submit job
- `-t <requested time>`: it is a normal Slurm argument for time request
- `-A <account>`: it is a normal Slurm argument for specifying which
  account to use
- `<Other normal Slurm arguments>`:
  - `-n <nomber of noded>`
  - `--ntasks-per-node=<ntasks-per-node>`
  - `--gres=<gres request>`
  - `--constraint=<features request>`
  - `--mem=<memory request>`
  - Try other `sbatch` arguments, they might work as well
- `pseudo.job`: should finished with script name, this also used in VC

``` bash
pwd
```

    ## /home/slurm/work/micro_cluster

## Run First Simulations

`slurmsim` is a utility for various Slurm simulation tasks. To run the
simulation, we will use the `run_sim` subcommand. Execute following:

``` bash
export CLUS_DIR=$(pwd)
export MACHINE_NAME="slurmsimcont"
export RUN_NAME="test1"
export dtstart=59
export replica=1

slurmsim -v run_sim  -d \
            -e ${CLUS_DIR}/etc \
            -a ${CLUS_DIR}/etc/sacctmgr.script \
            -w ${CLUS_DIR}/workload/small.events \
            -r ${CLUS_DIR}/results/${MACHINE_NAME}/${RUN_NAME}/dtstart_${dtstart}_${replica} \
            -dtstart $dtstart
```

        Logger initialization
        [INFO] Note: NumExpr detected 16 cores but "NUMEXPR_MAX_THREADS" not set, so enforcing safe limit of 8.
        [INFO] NumExpr defaulting to 8 threads.
        [INFO] Read from /home/slurm/work/micro_cluster/job_traces/small.events 20 even ts
        [INFO] slurm.conf: /home/slurm/work/micro_cluster/etc/slurm.conf
        [INFO] slurmdbd: /opt/slurm_sim/sbin/slurmdbd
        [INFO] slurmd: /opt/slurm_sim/sbin/slurmd
        [INFO] slurmctld: /opt/slurm_sim/sbin/slurmctld
        [INFO] dropping db from previous runs
        DROP DATABASE IF EXISTS slurmdb_micro
        [INFO] directory (/home/slurm/work/micro_cluster/log) does not exist, creating it 
        [INFO] deleting previous SlurmdbdPidFile file: /home/slurm/work/micro_cluster/var/slurmdbd.pid
        [INFO] deleting previous StateSaveLocation files from /home/slurm/work/micro_cluster/var/state
        [DEBUG] Set stdout/stderr for slurmctld to /home/slurm/work/micro_cluster/log/slurmctld_stdout.log
        [DEBUG] Set stdout/stderr for slurmdbd to /home/slurm/work/micro_cluster/log/slurmdbd_stdout.log
        [INFO] Launching slurmdbd
        [INFO] Running sacctmgr script from /home/slurm/work/micro_cluster/etc/sacctmgr.script
        sacctmgr: sacctmgr:  Modified qos...
          normal
        sacctmgr:  Adding QOS(s)
          supporters
         Settings
          Description    = supporters
          Priority                 = 100
        sacctmgr: sacctmgr:  Adding Cluster(s)
          Name           = micro
         Setting
          Default Limits:
          Fairshare     = 1
          QOS           = normal,supporters
        sacctmgr: sacctmgr:  Adding Account(s)
          account0
         Settings
          Description     = Account Name
          Organization    = Parent/Account Name
         Associations
          A = account0   C = micro     
         Settings
          Fairshare     = 100
          Parent        = root
        sacctmgr:  Adding Account(s)
          account1
         Settings
          Description     = Account Name
          Organization    = Parent/Account Name
         Associations
          A = account1   C = micro     
         Settings
          Fairshare     = 100
          Parent        = root
        sacctmgr:  Adding Account(s)
          account2
         Settings
          Description     = Account Name
          Organization    = Parent/Account Name
         Associations
          A = account2   C = micro     
         Settings
          Fairshare     = 100
          Parent        = root
        sacctmgr: sacctmgr:  Adding User(s)
          admin
         Settings =
          Default Account = account0
          Admin Level     = Administrator
         Associations =
          U = admin     A = account0   C = micro     
         Non Default Settings
          MaxSubmitJobs = 1000
        sacctmgr: sacctmgr:  Adding User(s)
          user1
         Settings =
          Default Account = account1
         Associations =
          U = user1     A = account1   C = micro     
         Non Default Settings
          MaxSubmitJobs = 1000
        sacctmgr:  Adding User(s)
          user2
         Settings =
          Default Account = account1
         Associations =
          U = user2     A = account1   C = micro     
         Non Default Settings
          MaxSubmitJobs = 1000
        sacctmgr:  Adding User(s)
          user3
         Settings =
          Default Account = account1
         Associations =
          U = user3     A = account1   C = micro     
         Non Default Settings
          MaxSubmitJobs = 1000
        sacctmgr:  Adding User(s)
          user4
         Settings =
          Default Account = account2
         Associations =
          U = user4     A = account2   C = micro     
         Non Default Settings
          MaxSubmitJobs = 1000
        sacctmgr:  Adding User(s)
          user5
         Settings =
          Default Account = account2
         Associations =
          U = user5     A = account2   C = micro     
         Non Default Settings
          MaxSubmitJobs = 1000
        sacctmgr: sacctmgr:  Modified user associations...
          C = micro      A = account2             U = user5    
          C = micro      A = account2             U = user4    
          C = micro      A = account1             U = user3    
          C = micro      A = account1             U = user2    
          C = micro      A = account1             U = user1    
          C = micro      A = account0             U = admin    
          C = micro      A = root                 U = root     
        sacctmgr: sacctmgr: sacctmgr: Account                 Cluster       User     Share 
        -------------------- ---------- ---------- --------- 
        root                      micro                    1 
         root                     micro       root         1 
         account0                 micro                  100 
          account0                micro      admin         1 
         account1                 micro                  100 
          account1                micro      user1         1 
          account1                micro      user2         1 
          account1                micro      user3         1 
         account2                 micro                  100 
          account2                micro      user4         1 
          account2                micro      user5         1 
        sacctmgr: 
        [INFO] Launching slurmctld
        ['/opt/slurm_sim/sbin/slurmctld', '-e', '/home/slurm/work/micro_cluster/job_traces/small.events', '-dtstart', '59']
        [INFO] Current time 1710513133.6579173
        [INFO] slurmdbd_create_time=1710513112.42
        [INFO] slurmctld_create_time=1710513128.36
        [INFO] slurmd_create_time=1710513127.36
        [INFO] Starting job submittion
        [INFO] Monitoring slurmctld until completion
        [INFO] All jobs submitted wrapping up
        [INFO] slurmctld took 30.056071043014526 seconds to run.
        first_line [2022-01-01T05:00:15.938834] error: Unable to open pidfile `/var/run/slurmctld.pid': Permission denied
         2022-01-01 05:00:15.938834 2022-01-01 05:00:15.938834
        last_line [2022-01-01T05:03:57.912788] All done.
         2022-01-01 05:03:57.912788 2022-01-01 05:03:57.912788
        [INFO] Copying results to :/home/slurm/work/micro_cluster/results/slurmsimcont/test1/dtstart_59_1
        [INFO] copying resulting file /home/slurm/work/micro_cluster/log/jobcomp.log to /home/slurm/work/micro_cluster/results/slurmsimcont/test1/dtstart_59_1
        [INFO] copying resulting file /home/slurm/work/micro_cluster/log/slurmctld.log to /home/slurm/work/micro_cluster/results/slurmsimcont/test1/dtstart_59_1
        [INFO] copying resulting file /home/slurm/work/micro_cluster/log/sched.log to /home/slurm/work/micro_cluster/results/slurmsimcont/test1/dtstart_59_1
        [DEBUG] Submit time for first job: 2022-01-01 05:01:14.315371
        [INFO] copying resulting file /home/slurm/work/micro_cluster/log/slurmctld_stdout.log to /home/slurm/work/micro_cluster/results/slurmsimcont/test1/dtstart_59_1
        [INFO] copying resulting file /home/slurm/work/micro_cluster/log/slurmdbd_stdout.log to /home/slurm/work/micro_cluster/results/slurmsimcont/test1/dtstart_59_1
        [INFO] Simulated time: 0:03:41.973954
        [INFO] Real time: 0:00:30.056383
        [INFO] Acceleration: 7.385252
        [INFO] Done

While it is running, we can take a look at specified arguments. First,
we started with setting some bash variables, which will be convenient
later when we automate runs for multiple simulations. We will go through
all of them and describe what it is and why we are doing it in this way.

``` bash
export CLUS_DIR=$(pwd)
```

It is convenient to specify pathways relative to our cluster simulation
directory:

``` bash
export MACHINE_NAME="slurmsimcont"
```

It specify machine name. Just like with real Slurm, the speed of actual
hardware can affect the scheduling, so it is helpful to track which
hardware was used for simulation.

``` bash
export RUN_NAME="test1"
```

`RUN_NAME` is used to label a particular test, for example, control,
high-priority, and so on.

``` bash
export dtstart=59
export replica=1
```

Due to *stochasticity*, we need to have multiple runs. We track them
with `replica` parameter for identical run and `dtstart` for additional
randomization.

`replica` parameter is usually having values like 1,2,3,….

`dtstart` specifies the time delay between the slurm controller start-up
and the first job submission. It is the main randomization mechanism in
Slurm Simulator.

The following arguments were used for `slurmsim` CLI:

- `-v` for extra messages
- `run_sim` command to run single Slurm simulation.
- `-d` remove results from the previous simulation
- `-e` specify the location of slurm `etc.` directory `slurm.conf` and
  friends should be where
- `-a` specify the sacctmgr script to set up accounts, users, qos and
  other things
- `-w` specify workload event file (a.k.a. job traces file)
- `-r` specify results storage directory, we use following format:
  `${CLUS_DIR}/results/${MACHINE_NAME}/${RUN_NAME}/dtstart_${dtstart}_${replica}`
- `-dtstart` specifies the time delay between the slurm controller
  start-up and the first job submission.

The `run_sim` command simplifies the execution of the Slurm Simulator.
It does the following:

1.  With `-d` option, it removes results from the previous simulation
    (clean DB, remove logs, shared memory, etc)
2.  Check the configuration files; some of the options are not supported
    in the Simulator, and some others should be set to a particular
    value. The configuration checking helps to run the simulation. Note
    that not everything is checked.
3.  Create missing directories
4.  Launch `slurmdbd`
5.  Execute `sacctmgr` script
6.  Launch `slurmctld` and start simulation
7.  On finishing `slurmctld` process termenate `slurmdbd`.
8.  Prepocess some outputs so that they can be loaded to R.
9.  Copy all resulting files to the results directory (set with `-r`
    option)

Now take a closer look at the output, you should be able to see the
above steps. At the end you will see something like this:

    [INFO] Simulated time: 0:03:41.973954
    [INFO] Real time: 0:00:30.056383
    [INFO] Acceleration: 7.3852

This informs you on simulated time and the time acceleration.

Take look at result directory:

``` bash
ls results/slurmsimcont/test1/dtstart_59_1
```

    ## jobcomp.log
    ## perf_profile.log
    ## perf_stat.log
    ## sched.log
    ## slurm_acct.out
    ## slurmctld.log
    ## slurmctld_log.csv
    ## slurmctld_stdout.log
    ## slurmdbd_stdout.log

    jobcomp.log
    perf_profile.log
    perf_stat.log
    sched.log
    slurm_acct.out
    slurmctld.log
    slurmctld_log.csv
    slurmctld_stdout.log
    slurmdbd_stdout.log

There are a lot of logs and output files:

- `sched.log` - scheduler log, usually emptyl
- `slurm_acct.out` - `sacct` output at the end of the simulation
- `jobcomp.log` - log from `jobcomp` plug-in
- `slurmctl.log` - log from `slurmctld`
- `slurmctld_stdout.log` - standard output and standard error from
  `slurmctld`, useful if simulation failed
- `slurmdbd_stdout.log` - standard output and standard error from
  `slurmdbd` daemon, useful if simulation failed
- `slurmctld_log.csv` - Slurm controller events generated from
  `slurmctld.log` processing

Lets take a look at `slurm_acct.out`

``` bash
head -n 5 results/slurmsimcont/test1/dtstart_59_1/slurm_acct.out
```

        JobID|JobIDRaw|Cluster|Partition|Account|Group|GID|User|UID|Submit|Eligible|Start|End|Elapsed|ExitCode|State|NNodes|NCPUS|ReqCPUS|ReqMem|ReqTRES|Timelimit|QOS|NodeList|JobName|NTasks
        1001|1001|micro|normal|account2|slurm|1000|user5|1005|2022-01-01T05:01:14|2022-01-01T05:01:14|2022-01-01T05:01:14|2022-01-01T05:01:14|00:00:00|0:0|COMPLETED|1|12|12|33600M|billing=12,cpu=12,mem=33600M,node=1|00:01:00|normal|b1|jobid_1001|
        1002|1002|micro|normal|account1|slurm|1000|user1|1001|2022-01-01T05:01:15|2022-01-01T05:01:15|2022-01-01T05:01:16|2022-01-01T05:02:16|00:01:00|0:0|TIMEOUT|1|1|1|2800M|billing=1,cpu=1,mem=2800M,node=1|00:01:00|normal|n1|jobid_1002|
        1003|1003|micro|normal|account2|slurm|1000|user4|1004|2022-01-01T05:01:16|2022-01-01T05:01:16|2022-01-01T05:01:16|2022-01-01T05:01:21|00:00:05|0:0|COMPLETED|1|1|1|500000M|billing=1,cpu=1,mem=500000M,node=1|00:01:00|normal|b1|jobid_1003|
        1004|1004|micro|normal|account1|slurm|1000|user3|1003|2022-01-01T05:01:30|2022-01-01T05:01:30|2022-01-01T05:01:30|2022-01-01T05:01:51|00:00:21|0:0|COMPLETED|2|24|24|67200M|billing=24,cpu=24,mem=67200M,node=1|00:01:00|normal|b1,g1|jobid_1004|

It contains information on compleded jobs. It will be used for our
analysis.

You also can find two new directories `log` and `var`. Thouse are used
temporary while Slurm Simulator is running all importent files are
eventually copied to results directory.

We rarely would have only one simulation (need statistics), so before
moving to results reading lets make another simulation:

``` bash
export CLUS_DIR=$(pwd)
export MACHINE_NAME="slurmsimcont"
export RUN_NAME="test1"
export dtstart=79
export replica=1

slurmsim -v run_sim  -d \
            -e ${CLUS_DIR}/etc \
            -a ${CLUS_DIR}/etc/sacctmgr.script \
            -w ${CLUS_DIR}/workload/small.events \
            -r ${CLUS_DIR}/results/${MACHINE_NAME}/${RUN_NAME}/dtstart_${dtstart}_${replica} \
            -dtstart $dtstart
```

## Read Results

Because we need to handle multiple runs simultaneously, we have
developed tools that help us with that. `read_sacct_out_multiple` will
read multiple `slurm_acct.out` from simulations with different start
times and replicas.

``` r
sacct <- read_sacct_out_multiple(
    slurm_mode="test1", # name of simulation
    results_root_dir="results/slurmsimcont/test1",
    dtstart_list=c(59, 79), # start time list
    run_id_list=1, # replicas list
    # sacct_out="slurm_acct.out"  # non-standard name of sacct_out
)
```

    ## Read:  results/slurmsimcont/test1/dtstart_59_1/slurm_acct.out 
    ## Read:  results/slurmsimcont/test1/dtstart_79_1/slurm_acct.out

``` r
sacct |> head()
```

<div class="kable-table">

| slurm_mode | dtstart | run_id | JobRecID | SubmitTime | StartTime | EndTime | WallTime | WaitTime | JobId | JobIdRaw |  GID |  UID | NodeCount | NCPUS | ReqCPUS | ReqTRES                              | NodeList | JobName    | NTasks | Submit              | Eligible            | Start               | End                 |          Elapsed |        Timelimit | Cluster | Partition | Account  | Group | User  | ExitCode | State     | QOS    | ReqMemSize | ReqMemPerNode |   SubmitTS |    StartTS |      EndTS | WaitHours | WallHours | NodeHours | WaitHours4log | WallHours4log |
|:-----------|--------:|-------:|---------:|-----------:|----------:|--------:|---------:|---------:|------:|---------:|-----:|-----:|----------:|------:|--------:|:-------------------------------------|:---------|:-----------|:-------|:--------------------|:--------------------|:--------------------|:--------------------|-----------------:|-----------------:|:--------|:----------|:---------|:------|:------|:---------|:----------|:-------|-----------:|:--------------|-----------:|-----------:|-----------:|----------:|----------:|----------:|--------------:|--------------:|
| test1      |      59 |      1 |     1001 |          0 |         0 |       0 |        0 |        0 |  1001 |     1001 | 1000 | 1005 |         1 |    12 |      12 | billing=12,cpu=12,mem=33600M,node=1  | b1       | jobid_1001 | NA     | 2022-01-01 05:01:14 | 2022-01-01 05:01:14 | 2022-01-01 05:01:14 | 2022-01-01 05:01:14 |               0s | 60s (~1 minutes) | micro   | normal    | account2 | slurm | user5 | 0:0      | COMPLETED | normal |      33600 | TRUE          | 1641013274 | 1641013274 | 1641013274 | 0.0000000 | 0.0000000 | 0.0000000 |     0.0166667 |     0.0166667 |
| test1      |      59 |      1 |     1002 |          1 |         2 |      62 |       60 |        1 |  1002 |     1002 | 1000 | 1001 |         1 |     1 |       1 | billing=1,cpu=1,mem=2800M,node=1     | n1       | jobid_1002 | NA     | 2022-01-01 05:01:15 | 2022-01-01 05:01:15 | 2022-01-01 05:01:16 | 2022-01-01 05:02:16 | 60s (~1 minutes) | 60s (~1 minutes) | micro   | normal    | account1 | slurm | user1 | 0:0      | TIMEOUT   | normal |       2800 | TRUE          | 1641013275 | 1641013276 | 1641013336 | 0.0002778 | 0.0166667 | 0.0166667 |     0.0166667 |     0.0166667 |
| test1      |      59 |      1 |     1003 |          2 |         2 |       7 |        5 |        0 |  1003 |     1003 | 1000 | 1004 |         1 |     1 |       1 | billing=1,cpu=1,mem=500000M,node=1   | b1       | jobid_1003 | NA     | 2022-01-01 05:01:16 | 2022-01-01 05:01:16 | 2022-01-01 05:01:16 | 2022-01-01 05:01:21 |               5s | 60s (~1 minutes) | micro   | normal    | account2 | slurm | user4 | 0:0      | COMPLETED | normal |     500000 | TRUE          | 1641013276 | 1641013276 | 1641013281 | 0.0000000 | 0.0013889 | 0.0013889 |     0.0166667 |     0.0166667 |
| test1      |      59 |      1 |     1004 |         16 |        16 |      37 |       21 |        0 |  1004 |     1004 | 1000 | 1003 |         2 |    24 |      24 | billing=24,cpu=24,mem=67200M,node=1  | b1,g1    | jobid_1004 | NA     | 2022-01-01 05:01:30 | 2022-01-01 05:01:30 | 2022-01-01 05:01:30 | 2022-01-01 05:01:51 |              21s | 60s (~1 minutes) | micro   | normal    | account1 | slurm | user3 | 0:0      | COMPLETED | normal |      67200 | TRUE          | 1641013290 | 1641013290 | 1641013311 | 0.0000000 | 0.0058333 | 0.0116667 |     0.0166667 |     0.0166667 |
| test1      |      59 |      1 |     1005 |         19 |        62 |      64 |        2 |       43 |  1005 |     1005 | 1000 | 1005 |         1 |    12 |      12 | billing=12,cpu=12,mem=500000M,node=1 | b1       | jobid_1005 | NA     | 2022-01-01 05:01:33 | 2022-01-01 05:01:33 | 2022-01-01 05:02:16 | 2022-01-01 05:02:18 |               2s | 60s (~1 minutes) | micro   | normal    | account2 | slurm | user5 | 0:0      | COMPLETED | normal |     500000 | TRUE          | 1641013293 | 1641013336 | 1641013338 | 0.0119444 | 0.0005556 | 0.0005556 |     0.0166667 |     0.0166667 |
| test1      |      59 |      1 |     1006 |         19 |        19 |      28 |        9 |        0 |  1006 |     1006 | 1000 | 1003 |         4 |    48 |      48 | billing=48,cpu=48,mem=134400M,node=1 | m\[1-4\] | jobid_1006 | NA     | 2022-01-01 05:01:33 | 2022-01-01 05:01:33 | 2022-01-01 05:01:33 | 2022-01-01 05:01:42 |               9s | 60s (~1 minutes) | micro   | normal    | account1 | slurm | user3 | 0:0      | COMPLETED | normal |     134400 | TRUE          | 1641013293 | 1641013293 | 1641013302 | 0.0000000 | 0.0025000 | 0.0100000 |     0.0166667 |     0.0166667 |

</div>

`read_sacct_out_multiple` also recalculates `SubmitTime`, `StartTime`
and `EndTime` in reference to the submission of first job.

`read_events_multiple` read events which ever extracted from slurmctrl
logs:

``` r
events_time <- read_events_multiple(
    slurm_mode="test1", # name of simulation
    results_root_dir="results/slurmsimcont/test1",
    dtstart_list=c(59, 79), # start time list
    run_id_list=1, # replicas list
    #events_csv="slurmctld_log.csv" # non-standard name of slurmctld_log.csv
)
```

    ## Read:  results/slurmsimcont/test1/dtstart_59_1/slurmctld_log.csv 
    ## Read:  results/slurmsimcont/test1/dtstart_79_1/slurmctld_log.csv

``` r
events_time |> head()
```

<div class="kable-table">

| ts                  | slurm_mode | dtstart | run_id | job_rec_id | metric                            |         t | value                         |
|:--------------------|:-----------|--------:|-------:|-----------:|:----------------------------------|----------:|:------------------------------|
| 2022-01-01 05:00:15 | test1      |      59 |      1 |         NA | slurm_start_time                  | -58.19048 | NA                            |
| 2022-01-01 05:00:16 | test1      |      59 |      1 |         NA | slurmctld_background              | -57.44375 | NA                            |
| 2022-01-01 05:00:17 | test1      |      59 |      1 |         NA | process_create_real_time          | -56.44371 | 2024-03-21T18:29:01.170       |
| 2022-01-01 05:00:17 | test1      |      59 |      1 |         NA | process_create_sim_time           | -56.44371 | 2022-01-01T05:00:15.472       |
| 2022-01-01 05:00:17 | test1      |      59 |      1 |         NA | queue_job_scheduler:from          | -56.44351 | \_slurm_rpc_node_registration |
| 2022-01-01 05:00:17 | test1      |      59 |      1 |         NA | queue_job_scheduler:job_sched_cnt | -56.44351 | 1                             |

</div>

## Make Events Plot

Let’s make a plot for starting times of our two simulations

``` r
plot_grid(
  ggplot(sacct, aes(
    x=SubmitTime,y=JobRecID,color=factor(dtstart),shape=factor(dtstart)))+
    geom_point() + scale_shape_manual(values = c(3,4)),
  ggplot(sacct, aes(
    x=StartTime,y=JobRecID,color=factor(dtstart),shape=factor(dtstart)))+
    geom_point() + scale_shape_manual(values = c(3,4)),
  labels = c("A","B"), nrow=2
)
```

![](readme_files/figure-gfm/submit_start-1.png)<!-- -->

You can find that even though the submit time is the same between two
realizations, the start time can be substantially different.

What are the reasons for such behavior? Many Slurm routines are executed
in a cyclic manner: some will go to sleep for a predefined amount of
time before repeating the cycle, and others will check from time to time
if a predefined amount of time passed since the last time the cycle was
started.

For example, the function that kills jobs running over the requested
wall time starts a new cycle if 30 seconds have passed from the last
run, and then it will check all jobs. The thread that does the job also
does other things, so the time between checks is not always exactly 30
seconds.

In addition, we don’t know apriori at which stage of these varying
stop-and-start cycles the job submission ended up. So we have to try all
different possibilities and report an average behavior.

To identify what exactly went differently we can use event diagram:

``` r
make_events_diagramm(
  events_time |> filter(slurm_mode=="test1" & dtstart==59 & run_id==1L),
  events_time |> filter(slurm_mode=="test1" & dtstart==79 & run_id==1L)
)
```

    ## Warning in RColorBrewer::brewer.pal(N, "Set2"): minimal value for n is 3, returning requested palette with 3 different levels

    ## Warning in RColorBrewer::brewer.pal(N, "Set2"): minimal value for n is 3, returning requested palette with 3 different levels

![](readme_files/figure-gfm/events_diagramm-1.png)<!-- -->

The event diagram shows most events important for scheduling. X-axis
shows the time, zero corresponds to the submission time of first job.
The jobs submit, start and end time are show as horizontal segments and
the y-axis correspond to job-id. The diagram allow comparison of two
simulations the jobs from first one is slightly below the second one.
The jobs horizontal segment starts with submit time (grey circle),
followed by start time (blue plus if scheduled by main scheduler and
green plus if scheduled by backfiller) and ends with jobs finish time
(red cross). The segment between submit time and start time is
highlighted by grey segment line and from start to end time by red line.
Different scheduler related events are also shown by vertical lines at
time they occur. The events from first simulation are shown by solid
line and events from second by dash line. Different event are shown by
different colors. This is interactive plot, click/double click on legend
or plot to hide or select the plots elements.

# Run and Analyse Multiple Independent Simulations

Due to stochasticity we have to run multiple simulations and report on
averaged numbers. So we need somehow to randomize each run, we are doing
it by randomizing the time between the simulation start and the
submission of first jobs (relative time between jobs stays the same).

## Generate Random Start Times Delay

Lets get these random start times delay (additional time between start
time of first job and starting time of `slurmctld`):

``` python
# Note that this is a python chunk
# generate random start time for small
import numpy as np
np.random.seed(seed=20211214)
start_times = np.random.randint(low=30, high=150, size=10)
" ".join([str(v) for v in start_times])
```

    ## '59 58 99 126 79 89 146 105 114 68'

I got ‘59 58 99 126 79 89 146 105 114 68’.

## Run the Similations

Now run them all:

``` bash
export CLUS_DIR=$(pwd)
export MACHINE_NAME="slurmsimcont"

export RUN_NAME="test2"

export dtstarts='59 58 99 126 79 89 146 105 114 68'
export run_ids=1

export SLURM_ETC="${CLUS_DIR}/etc"
export SACCTMGR_SCRIPT="${CLUS_DIR}/etc/sacctmgr.script"
export WORKLOAD="${CLUS_DIR}/workload/small.events"

# Do simulation
export RESULTS_ROOT_DIR="${CLUS_DIR}/results/${MACHINE_NAME}/${RUN_NAME}"
rm -rf ${RESULTS_ROOT_DIR}
mkdir -p ${RESULTS_ROOT_DIR}

for replica in $run_ids
do
    for dtstart in $dtstarts
    do
        echo "#######################################"
        echo "Start dtstart $dtstart replica $replica"
        slurmsim -v run_sim  -d \
            -e ${SLURM_ETC} \
            -a ${SACCTMGR_SCRIPT} \
            -w ${WORKLOAD} \
            -r ${RESULTS_ROOT_DIR}/dtstart_${dtstart}_${replica} \
            -dtstart $dtstart >> ${RESULTS_ROOT_DIR}/slurmsim.log
    done
done

# Copy config for reference
cp -r ${SLURM_ETC} ${RESULTS_ROOT_DIR}
cp ${WORKLOAD} ${RESULTS_ROOT_DIR}
cp ${SACCTMGR_SCRIPT} ${RESULTS_ROOT_DIR}
```

## Read Results

``` r
sacct <- read_sacct_out_multiple(
    slurm_mode="test2", # name of simulation
    results_root_dir="results/slurmsimcont/test2",
    dtstart_list=c(59, 58, 99, 126, 79, 89, 146, 105, 114, 68), # start time list
    run_id_list=1, # replicas list
    # sacct_out="slurm_acct.out"  # non-standard name of sacct_out
)
```

    ## Read:  results/slurmsimcont/test2/dtstart_59_1/slurm_acct.out 
    ## Read:  results/slurmsimcont/test2/dtstart_58_1/slurm_acct.out 
    ## Read:  results/slurmsimcont/test2/dtstart_99_1/slurm_acct.out 
    ## Read:  results/slurmsimcont/test2/dtstart_126_1/slurm_acct.out 
    ## Read:  results/slurmsimcont/test2/dtstart_79_1/slurm_acct.out 
    ## Read:  results/slurmsimcont/test2/dtstart_89_1/slurm_acct.out 
    ## Read:  results/slurmsimcont/test2/dtstart_146_1/slurm_acct.out 
    ## Read:  results/slurmsimcont/test2/dtstart_105_1/slurm_acct.out 
    ## Read:  results/slurmsimcont/test2/dtstart_114_1/slurm_acct.out 
    ## Read:  results/slurmsimcont/test2/dtstart_68_1/slurm_acct.out

``` r
events_time <- read_events_multiple(
    slurm_mode="test2", # name of simulation
    results_root_dir="results/slurmsimcont/test2",
    dtstart_list=c(59, 58, 99, 126, 79, 89, 146, 105, 114, 68), # start time list
    run_id_list=1, # replicas list
    #events_csv="slurmctld_log.csv" # non-standard name of slurmctld_log.csv
)
```

    ## Read:  results/slurmsimcont/test2/dtstart_59_1/slurmctld_log.csv 
    ## Read:  results/slurmsimcont/test2/dtstart_58_1/slurmctld_log.csv 
    ## Read:  results/slurmsimcont/test2/dtstart_99_1/slurmctld_log.csv 
    ## Read:  results/slurmsimcont/test2/dtstart_126_1/slurmctld_log.csv 
    ## Read:  results/slurmsimcont/test2/dtstart_79_1/slurmctld_log.csv 
    ## Read:  results/slurmsimcont/test2/dtstart_89_1/slurmctld_log.csv 
    ## Read:  results/slurmsimcont/test2/dtstart_146_1/slurmctld_log.csv 
    ## Read:  results/slurmsimcont/test2/dtstart_105_1/slurmctld_log.csv 
    ## Read:  results/slurmsimcont/test2/dtstart_114_1/slurmctld_log.csv 
    ## Read:  results/slurmsimcont/test2/dtstart_68_1/slurmctld_log.csv

## Analyse the Results

``` r
plot_grid(
  ggplot(sacct, aes(
    x=SubmitTime,y=JobRecID))+
    geom_point(alpha=0.2),
  ggplot(sacct, aes(
    x=StartTime,y=JobRecID))+
    geom_point(alpha=0.2),
  labels = c("A","B"), nrow=2
)
```

![](readme_files/figure-gfm/submit_start2-1.png)<!-- --> In the plot
above the submit time (A) and start time (B) for each job (shown on
X-Axis) are overlayed from the ten independent runs. Note that submit
times relative to the first job are exactly the same but the start time
can be almost deterministic (jobs 1001,1002,1003,1004 and 1009), vary a
little (jobs 1005-1008, 1011-1013,1016,1018-1020) or vary a lot (jobs
1010,1014,1015,1017). In lager HPC resources with longer jobs and high
resource utilization the starting time difference can be substantial.

Next: [Medium Cluster Tutorial](./medium_cluster/)
