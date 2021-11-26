# Centos-7 based Slurm WLM for Modeling with Docker

Set of containers to rum Slurm in Docker for modeling purposes

## Creating Images

> Docker build should be executed in root of slurm-model directory
> (one level up from here)


### Making Slurm RPMs

First we need slurm RPMs.

MakeSlurmRPM.Dockerfile describes simple image for centos 7 rpm making.
Here is listing on the whole process:

```bash
# create directory for RPMS storage
[[ ! -d "./docker/virtual_cluster/RPMS" ]] && mkdir -p docker/virtual_cluster/RPMS
rm -rf "./docker/virtual_cluster/RPMS/*"

# make image
docker build --no-cache -t pseudo/slurm_rpm_maker:latest -f ./docker/virtual_cluster/MakeSlurmRPM.Dockerfile .

# make slurm RPMS from default tarball
docker run --name slurm_rpm_maker -h slurm_rpm_maker \
           -v `pwd`/docker/virtual_cluster/RPMS:/RPMS \
           --rm \
           -it pseudo/slurm_rpm_maker:latest make_slurm_rpms
# (if needed instead) debug version
docker run --name slurm_rpm_maker -h slurm_rpm_maker \
           -v `pwd`/docker/virtual_cluster/RPMS:/RPMS \
           --rm \
           -it pseudo/slurm_rpm_maker:latest -c "make_slurm_rpms debug"
```

## Making Images for Head-Node and Compute-Nodes

```bash
# Build Common Image
docker build --no-cache -f docker/virtual_cluster/Common.Dockerfile -t nsimakov/slurm_common:2 .
# (Optionally) Run Common container to test it
# docker run -it --rm -h compute000 -p 222:22 --name compute000 nsimakov/slurm_common:latest

# Build Head-Node Image
docker build --no-cache -f docker/virtual_cluster/HeadNode.Dockerfile -t nsimakov/slurm_head_node:2 .
# (Optionally) Run Head-Node container to test it
# docker run -it --rm -h head-node -p 222:22 --name head-node nsimakov/slurm_head_node:latest

# Build Compute-Node Image
docker build --no-cache -f docker/virtual_cluster/ComputeNode.Dockerfile -t nsimakov/slurm_compute_node:2 .
# (Optionally) Run Compute-Node container to test it
# docker run -it --rm -h compute000 -p 222:22 --name compute000 nsimakov/slurm_compute_node:latest
```




Initial sizes:
pseudo/slurm_common:1 588542281
pseudo/slurm_head_node:1 1046462804
pseudo/slurm_compute_node:1 869'013'024

* no update
* no python g++ vim mc and all other helpers
pseudo/slurm_common:2 240020608
pseudo/slurm_compute_node: 392316592
pseudo/slurm_compute_node:  351144115
