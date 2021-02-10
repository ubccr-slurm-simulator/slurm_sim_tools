#!/usr/bin/env bash
SLURM_WORKDIR_BIN="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
export SLURM_WORKDIR="$( dirname ${SLURM_WORKDIR_BIN})"
export SLURM_DIR=SLURM_DIR
export SLURM_CONF=$SLURM_WORKDIR/etc/slurm.conf
export PATH=$SLURM_DIR/bin:$SLURM_DIR/sbin:$PATH
