Slurm Simulator Tutorial
================
<nikolays@buffalo.edu>
28 May, 2024

- [Overview](#overview)
  - [Some vocabulary](#some-vocabulary)
- [Installation](#installation)
  - [Install proper docker on your
    System](#install-proper-docker-on-your-system)
  - [Run Slurm Container](#run-slurm-container)
    - [The Simplest: Just to Try It, Good to Do
      Tutorial](#the-simplest-just-to-try-it-good-to-do-tutorial)
    - [For Actual work: With X11 Forwarding and Directories
      Binding](#for-actual-work-with-x11-forwarding-and-directories-binding)
    - [For Development work: With X11 Forwarding and Directories
      Binding](#for-development-work-with-x11-forwarding-and-directories-binding)
    - [Users Id Mapping](#users-id-mapping)
- [Get Tutorial Files and Starting
  Tutorial](#get-tutorial-files-and-starting-tutorial)

# Overview

This tutorial is for Slurm Simulator version 3.0, which is based on
Slurm-23.02.

We support two approaches for Slurm modeling:

1.  Slurm Simulator is a modified Slurm code allowing time-accelerated
    simulation. That is, one month of workload can be done in hours
    (subject to system size and workload).

2.  A Virtual Cluster (VC) is a cluster built within Docker in which
    each compute and head node is modeled by its own container. The
    Slurm code is unmodified. It does not allow time-accelerated
    simulation; that is, calculating one month’s workload would take a
    month. VC is largely used by us to calculate reference workload
    realization.

Both approaches use same format to specify submitted jobs (events file).

Here we will concentrate on Slurm Simulator.

## Some vocabulary

Here is some terminology we used and the meaning we place into it.

**Workload** describes all compute jobs that HPC resources need to do.
It is also referred to as **job traces**.

**Workload realization** is a particular way in which the workload was
processed by HPC resources. That is, now we know the job starting times
and which nodes were used. Due to stochasticity the same workload on the
same HPC resource with the same Slurm configuration can have different
workload realization.

**Events File** - a file to specify users’ jobs and other events.

# Installation

The easiest way to start using Slurm Simulator is by using a docker
container. The Slurm simulator container contains Slurm simulator
binaries and all necessary libraries and tools for running the
simulator, analyzing results, and doing full development.

The Slurm simulator container is built on top of
<https://github.com/jupyter/docker-stacks> with bits from
<https://github.com/rocker-org/rocker-versioned>.

The provided container has `mariadb` with user account `slurm` and
password `slurm`. The password for user `slurm` is `slurm`.

## Install proper docker on your System

Look at <https://www.docker.com/> for details.

## Run Slurm Container

The username within the container is `slurm`, and the password is also
`slurm`. For security reasons, keep the container local or do ssh-port
forwarding.

The container uses port 8888 for Jupyter Lap and 8787 for the RStudio
server.

To access Jupyter Lab, use the URL provided after launch in output. For
RStudio, go to <http://localhost:8787>.

### The Simplest: Just to Try It, Good to Do Tutorial

``` bash
docker run -p 0.0.0.0:8888:8888 0.0.0.0:8787:8787 -it \
    --name slurmsim -h slurmsim \
    nsimakov/slurm_sim:v3.0
```

Use the shown URL to start Jupyter Lab.

### For Actual work: With X11 Forwarding and Directories Binding

The following is working on WSL (don’t forget to start docker and enable
integration with your distros):

``` bash
docker run -p 0.0.0.0:8888:8888 0.0.0.0:8787:8787 -it --rm \
    --name slurmsim -h slurmsim \
    -v <persistent storage on host>:/home/slurm/work \
    -v /tmp/.X11-unix:/tmp/.X11-unix -v /mnt/wslg:/mnt/wslg \
    -e DISPLAY=$DISPLAY -e WAYLAND_DISPLAY=$WAYLAND_DISPLAY \
    -e XDG_RUNTIME_DIR=$XDG_RUNTIME_DIR -e PULSE_SERVER=$PULSE_SERVER \
    nsimakov/slurm_sim:v3.0
```

### For Development work: With X11 Forwarding and Directories Binding

``` bash
# lets keep all in ~/slurm_sim_wsp
mkdir -p $HOME/slurm_sim_wsp
cd $HOME/slurm_sim_wsp
# Get Slurm Simulator tools
git clone --recurse-submodules git@github.com:ubccr-slurm-simulator/slurm_sim_tools.git
```

``` bash
docker run -p 0.0.0.0:8888:8888 -p 0.0.0.0:8787:8787 -it --rm \
    --name slurmsim -h slurmsim \
    -v $HOME/slurm_sim_wsp:/home/slurm/slurm_sim_wsp \
    -v $HOME/slurm_sim_wsp/slurm_sim_tools/tutorials:/home/slurm/work \
    -v $HOME/slurm_sim_wsp/slurm_sim_tools:/opt/slurm_sim_tools \
    -v /tmp/.X11-unix:/tmp/.X11-unix -v /mnt/wslg:/mnt/wslg \
    -e DISPLAY=$DISPLAY -e WAYLAND_DISPLAY=$WAYLAND_DISPLAY \
    -e XDG_RUNTIME_DIR=$XDG_RUNTIME_DIR -e PULSE_SERVER=$PULSE_SERVER \
    nsimakov/slurm_sim:v3.0
```

### Users Id Mapping

In case if your user-id and group-id is not 1000, then you can add the
following:

        -e NB_USER="slurm" \
        -e NB_UID="<user id>" \
        -e NB_GROUP="slurm" \
        -e NB_GID="<group id>" \
        -e CHOWN_HOME=yes \

I am not sure about CHOWN_HOME and keep NB_USER and NB_GROUP default to
slurm.

Because the container is built on top of
<https://github.com/jupyter/docker-stacks> it supports some of the
docker-stacks magics.

# Get Tutorial Files and Starting Tutorial

If you haven’t did it alread launch RStudio server at
<http://localhost:8787> (username is `slurm` and password is also
`slurm`). In the terminal window copy all tutorial files to
`/home/slurm/work`:

``` bash
cd /home/slurm/work
cp -r /opt/slurm_sim_tools/tutorials/* /home/slurm/work/
```

Get to `/home/slurm/work/micro_cluster` directory and start
`micro_cluster_tutorial.Rmd` notebook. Follow the directions in a
notebook.

[Next: Micro Cluster
Tutorial](./micro_cluster/micro_cluster_tutorial.md)
