#!/bin/bash

# This script gets the basic things running to be able to work with the slurm simulator

echo "Setting up......."

rstudio-server start # starts up rstudio server right away

# this starts up sshd
cmd_start sshd
cmd_start mysqld  # starts up mysql to use

echo "Rstudio server, sshd, and mysql all set up"




