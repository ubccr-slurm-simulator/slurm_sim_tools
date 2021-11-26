#!/bin/bash
# build all images

CUR_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SLURM_MODEL_DIR="$( dirname "${CUR_DIR}" )"

#exit on any error
set -e

cd "${SLURM_MODEL_DIR}"

# Making Slurm RPMs
[[ -d "${SLURM_MODEL_DIR}/docker/RPMS" ]] && rm -rf "${SLURM_MODEL_DIR}/docker/RPMS"
rm -rf "${SLURM_MODEL_DIR}/docker/RPMS/*"

# make image
docker build -t pseudo/slurm_rpm_maker:latest -f ./docker/MakeSlurmRPM.Dockerfile .
docker run --name slurm_rpm_maker -h slurm_rpm_maker \
           -v `pwd`/docker/RPMS:/RPMS:Z \
           --rm \
           -it pseudo/slurm_rpm_maker:latest make_slurm_rpms

# Build Common Image
docker build -f docker/Common.Dockerfile -t pseudo/slurm_common:latest .

# Build Head-Node Image
docker build -f docker/HeadNode.Dockerfile -t pseudo/slurm_head_node:latest .

# Build Compute-Node Image
docker build -f docker/ComputeNode.Dockerfile -t pseudo/slurm_compute_node:latest .

