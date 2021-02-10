#!/usr/bin/env bash
SLURM_WORKDIR_BIN="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
source ${SLURM_WORKDIR_BIN}/env.sh

slurmdbd -Dvvvv
