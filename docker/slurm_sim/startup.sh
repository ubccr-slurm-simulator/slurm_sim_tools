#!/bin/bash

# This script gets the basic things running to be able to work with the slurm simulator

echo "Starting daemons ......."

sudo rstudio-server start # starts up rstudio server right away

# this starts up sshd
sudo /usr/local/bin/cmd_start sshd
sudo /usr/local/bin/cmd_start mysqld  # starts up mysql to use

echo "Rstudio server, sshd, and mysql all set up"

if [ $# -ne 0 ]
then
    cmd_start $@
fi

if [ -t 0 ] ; then
    echo "Interactive run, starting bash-shell"
    /bin/bash
else
    echo "not interactive run"
    echo "All requested daemon launched"
    while true; do
         sleep 60
    done
fi
