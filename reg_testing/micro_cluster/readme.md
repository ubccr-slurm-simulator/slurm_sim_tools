

```bash
docker build -f reg_testing/micro_cluster/docker/SlurmFronEnd.Dockerfile \
    -t slurm_front_end:slurm-20.02-sim .

docker run --name slurm -h slurm \
   --rm \
   -v $(pwd)/reg_testing/micro_cluster/docker/etc:/usr/local/etc \
   -v $(pwd):/home/slurm/slurm_sim_tools \
   -it pseudo/slurm_front_end:slurm-20.02-sim
mkdir bld
cd bld
~/slurm_simulator/configure --prefix=/usr/local --disable-x11 --enable-front-end --with-hdf5=no 

~/slurm_sim_tools/src/run_slurm.py -s /usr -e /etc/slurm -t /etc/slurm/sim.events -r ~/results  -v

sudo ~/slurm_sim_tools/src/run_slurm.py -s /usr -e /etc/slurm -t /etc/slurm/sim.events -r ~/results -a /etc/slurm/sacctmgr.sh -d -v -dtstart 0

sudo ~/slurm_sim_tools/src/run_slurm.py -s /usr -e /etc/slurm -t /etc/slurm/test_trace.events \
    -r ~/results/test_trace/dtstart_10_1 -a /etc/slurm/sacctmgr.sh \
    -d -v -dtstart 10 &> test_trace_dtstart_10_1.log &
tail -f test_trace_dtstart_10_1.log

sudo ~/slurm_sim_tools/src/run_slurm.py -s /usr -e /etc/slurm -t /etc/slurm/test_trace_shrinked.events \
    -r ~/results/test_trace_shrinked/dtstart_10_1 -a /etc/slurm/sacctmgr.sh \
    -d -v -dtstart 10 &> test_trace_shrinked_dtstart_10_1.log

sudo /opt/slurm_sim_tools/src/run_slurm.py -s /opt/slurm_front_end -e /opt/cluster/micro1/etc \
    -t /opt/cluster/micro1/etc/test_trace_shrinked.events \
    -r ~/results/test_trace_shrinked/dtstart_10_3 -a /opt/cluster/micro1/etc/sacctmgr.sh \
    -d -v -dtstart 10 &> test_trace_shrinked_dtstart_10_3.log

docker build -f reg_testing/micro_cluster/docker/SlurmFronEnd.Dockerfile -t nsimakov/slurm_vc:slurm-20.02-sim .

nohup docker run --name slurm -h slurm --rm -v $HOME/results:/root/results \
    nsimakov/slurm_vc:slurm-20.02-sim sshd munged mysqld \
    /opt/bin/run_test_trace_front_end.sh &>  run_test_trace_front_end.out &

nohup docker run --name slurm -h slurm --rm -v $HOME/results:/root/results \
    nsimakov/slurm_vc:slurm-20.02-sim sshd munged mysqld \
    /opt/bin/run_test_trace_shrinked_front_end.sh &>  run_test_trace_shrinked_front_end.out &


singularity build slurm_front_end.sif docker-daemon://pseudo/slurm_front_end:slurm-20.02-sim

```