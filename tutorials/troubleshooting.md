# Notebook, Running 
## Exception: slurmdbd is running

```
Exception: slurmdbd is running. Previous simulation might still be up. Kill the process if you sure that it shouldn't be up.
```

Solution: kill slurmdbd

```
>ps -Af 
UID        PID  PPID  C STIME TTY          TIME CMD
slurm      539     1  4 21:24 ?        00:00:12 /opt/slurm_sim/sbin/slurmdbd -Dvv
slurm     1245  1021  0 21:28 pts/2    00:00:00 ps -Af
> kill -9 539
```

# slurmctld
## Fatal Errors
### slurmctld: fatal: Unable to determine this slurmd's NodeName

`FrontEndName` can not be resolved

```ini
FrontEndName=bumblebee
```