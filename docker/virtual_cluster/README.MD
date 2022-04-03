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
docker build -t pseudo/slurm_rpm_maker:latest -f ./docker/virtual_cluster/MakeSlurmRPM.Dockerfile .

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

# make slurm RPMS from slurm_simulator code
docker run --name slurm_rpm_maker -h slurm_rpm_maker \
           -v `pwd`/docker/virtual_cluster/RPMS:/RPMS \
           -v `pwd`/slurm_simulator:/root/slurm-21.08.4 \
           --rm \
           -it pseudo/slurm_rpm_maker:latest make_slurm_rpms_simsource
```

## Making Images for Head-Node and Compute-Nodes

container versions:
* version 2 corresponds to 21.08.4
* version 3 corresponds to 21.08.4 but sim source code

```bash
# Build Common Image
docker build -f docker/virtual_cluster/Common.Dockerfile -t nsimakov/slurm_common:1 .
# (Optionally) Run Common container to test it
# docker run -it --rm -h compute000 -p 222:22 --name compute000 nsimakov/slurm_common:latest

# Build Head-Node Image
docker build -f docker/virtual_cluster/HeadNode.Dockerfile -t nsimakov/slurm_head_node:1 .
# (Optionally) Run Head-Node container to test it
# docker run -it --rm -h head-node -p 222:22 --name head-node nsimakov/slurm_head_node:latest

# Build Compute-Node Image
docker build -f docker/virtual_cluster/ComputeNode.Dockerfile -t nsimakov/slurm_compute_node:1 .
# (Optionally) Run Compute-Node container to test it
# docker run -it --rm -h compute000 -p 222:22 --name compute000 nsimakov/slurm_compute_node:latest

docker push nsimakov/slurm_head_node:1
docker push nsimakov/slurm_compute_node:1

```

## Making Images for Slurm Simulator Dev Head Node
```bash
# Build Slurm Simulator Dev Head Node Image
docker build -f docker/virtual_cluster/SlurmSimNodeDev.Dockerfile -t nsimakov/slurm_sim_head_node:dev .
# (Optionally) Run Slurm Simulator Dev Head Node container to test it
# docker run -it --rm -h head-node -p 222:22 --name head-node nsimakov/slurm_sim_head_node:dev

docker push nsimakov/slurm_sim_head_node:dev

cd /home/nikolays/slurm_sim_ws/slurm_model/micro3
docker run -it --rm -h headnode -p 222:22 --name headnode -v ./etc:/etc/slurm nsimakov/slurm_sim_head_node:dev
```
## PCP
```bash
sudo vim /etc/yum.repos.d/performancecopilot.repo

[performancecopilot]
name=Performance Co-Pilot
baseurl=https://performancecopilot.jfrog.io/artifactory/pcp-rpm-release/centos/$releasever/$basearch
enabled=1
gpgcheck=0
gpgkey=https://performancecopilot.jfrog.io/artifactory/pcp-rpm-release/centos/$releasever/$basearch/repodata/repomd.xml.key
repo_gpgcheck=1
```

```bash
sudo yum install -y dnf
sudo dnf install -y pcp-zeroconf

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

# Singularity 
## Singularity Installation

```bash
export VERSION=1.18 OS=linux ARCH=amd64 && \  # Replace the values as needed
wget https://dl.google.com/go/go$VERSION.$OS-$ARCH.tar.gz && \ # Downloads the required Go package
sudo tar -C /usr/local -xzvf go$VERSION.$OS-$ARCH.tar.gz && \ # Extracts the archive
rm go$VERSION.$OS-$ARCH.tar.gz    # Deletes the ``tar`` file

echo 'export PATH=/usr/local/go/bin:$PATH' >> ~/.bashrc && \
source ~/.bashrc

export VERSION=3.9.7 && # adjust this as necessary \
    wget https://github.com/sylabs/singularity/releases/download/v${VERSION}/singularity-ce-${VERSION}.tar.gz && \
    tar -xzf singularity-ce-${VERSION}.tar.gz && \
    cd singularity-ce-${VERSION}
./mconfig && \
    make -C builddir && \
    sudo make -C builddir install
```

## Singularity Containers

```bash

docker build -f docker/virtual_cluster/SlurmSim.Dockerfile -t nsimakov/slurm_sim:dev .
docker push nsimakov/slurm_sim:dev
sudo singularity build ../slurmsim.sif docker-daemon://nsimakov/slurm_sim:dev
scp ../slurmsim.sif anvil:/anvil/projects/x-ccr120014/ssim

mkdir results

# rm -rf log  log_loc  munge var results mysql

#SBATCH --partition=standard
##SBATCH --qos=cpu
#SBATCH --nodes=2
#SBATCH --ntasks-per-node=128
#SBATCH --time=00:13:00
#SBATCH --output=/anvil/scratch/x-xdtas/akrr_data/anvil/namd/2022.03.22.15.21.59.337438/stdout
#SBATCH --error=/anvil/scratch/x-xdtas/akrr_data/anvil/namd/2022.03.22.15.21.59.337438/stderr
#SBATCH --exclusive

for((run_id=1;run_id<=10;run_id=run_id+1))
do
singularity exec \
    --bind ${PWD}/run_${run_id}/mysql/var/log/mysql:/var/log/mariadb \
    --bind ${PWD}/run_${run_id}/mysql/var/lib/mysql:/var/lib/mysql \
    --bind ${PWD}/run_${run_id}/mysql/run/mysqld:/run/mariadb \
    --bind ${PWD}/run_${run_id}/munge/log:/var/log/munge \
    --bind ${PWD}/run_${run_id}/munge/run:/run/munge \
    --bind ${PWD}/run_${run_id}/munge/var:/var/lib/munge \
    --bind ${PWD}/run_${run_id}/munge/etc:/etc/munge \
    --bind ${PWD}/run_${run_id}:/workdir \
    ./slurmsim.sif start_sim_cont ${run_id} &
    pids[${i}]=$!
done

# wait for all pids
for pid in ${pids[*]}; do
    wait $pid
done

run_id=1
rm -rf run* out* slurm*.out results/*

for((run_id=1;run_id<=10;run_id=run_id+1))
do
mkdir -p ./run_${run_id}/etc_sim
cp ./etc_sim/* ./run_${run_id}/etc_sim
sed -i "s/SlurmctldPort=6200/SlurmctldPort=$((6200+${run_id}))/g" ./run_${run_id}/etc_sim/slurm.conf
sed -i "s/SlurmdPort=6300/SlurmdPort=$((6300+${run_id}))/g" ./run_${run_id}/etc_sim/slurm.conf
sed -i "s/AccountingStoragePort=6400/AccountingStoragePort=$((6400+${run_id}))/g" ./run_${run_id}/etc_sim/slurm.conf
sed -i "s/DbdPort=6400/DbdPort=$((6400+${run_id}))/g" ./run_${run_id}/etc_sim/slurmdbd.conf
sed -i "s/StoragePort=3360/StoragePort=$((3400+${run_id}))/g" ./run_${run_id}/etc_sim/slurmdbd.conf

sed -i "s/SlurmUser=slurm/SlurmUser=$USER/g" ./run_${run_id}/etc_sim/slurm.conf
sed -i "s/SlurmUser=slurm/SlurmUser=$USER/g" ./run_${run_id}/etc_sim/slurmdbd.conf

mkdir -p ./run_${run_id}/mysql/var/lib/mysql ./run_${run_id}/mysql/var/log/mysql ./run_${run_id}/mysql/run/mysqld
mkdir -p ./run_${run_id}/var/spool ./run_${run_id}/var/state ./run_${run_id}/log 
mkdir -p ./run_${run_id}/munge/log ./run_${run_id}/munge/run ./run_${run_id}/munge/var ./run_${run_id}/munge/etc
echo "secret munge key secret munge key secret munge key" > ./run_${run_id}/munge/etc/munge.key
done

sbatch batch.sh



run_id=1
singularity exec \
    --bind ${PWD}/run_${run_id}/mysql/var/log/mysql:/var/log/mariadb \
    --bind ${PWD}/run_${run_id}/mysql/var/lib/mysql:/var/lib/mysql \
    --bind ${PWD}/run_${run_id}/mysql/run/mysqld:/run/mariadb \
    --bind ${PWD}/run_${run_id}/munge/log:/var/log/munge \
    --bind ${PWD}/run_${run_id}/munge/run:/run/munge \
    --bind ${PWD}/run_${run_id}/munge/var:/var/lib/munge \
    --bind ${PWD}/run_${run_id}/munge/etc:/etc/munge \
    --bind ${PWD}/run_${run_id}:/workdir \
    ~/slurm_sim_ws/slurmsim.sif ls

chmod 700 /var/log/munge /var/lib/munge /etc/munge
chmod 600 /etc/munge/munge.key 
chmod 755 /run/munge
munged
# instal db
mysql_install_db

# start server
mysqld_safe --nowatch --port=3400
# wait till it be active
mysqladmin --wait=30 --host=localhost --port=3400 ping

# add slurm user
mysql -e "CREATE USER 'slurm'@'%' IDENTIFIED BY 'slurm';" -u root
mysql -e 'GRANT ALL PRIVILEGES ON *.* TO "slurm"@"%" WITH GRANT OPTION;' -u root
mysql -e "CREATE USER 'slurm'@'localhost' IDENTIFIED BY 'slurm';" -u root
mysql -e 'GRANT ALL PRIVILEGES ON *.* TO "slurm"@"localhost" WITH GRANT OPTION;' -u root


MACHINE_NAME=`hostname`
RUN_NAME=workload
dtstart=261
replica=1

export SLURM_SIM_DIR=/usr
export SLURM_CONF=/home/nikolays/slurm_sim_ws/slurm_model/ubhpc/singularity/etc_sim/slurm.conf
export PATH=/home/nikolays/slurm_sim_ws/slurm_sim_tools/bin:$SLURM_SIM_DIR/bin:$SLURM_SIM_DIR/sbin:$PATH
#/usr/sbin/slurmctld
CLUS_DIR=`pwd`
  >& ./results/${MACHINE_NAME}/${RUN_NAME}/dtstart_${dtstart}_${replica}.out


workload=$SCRIPT_DIR/job_traces/workload.events
run_ids="1"
dtstarts="55 137 37 232 234 49 79 241 71 261"




export SLURM_SIM_DIR=/usr
export SLURM_CONF=/home/nikolays/slurm_sim_ws/slurm_model/ubhpc/singularity/etc_sim/slurm.conf
export PATH=/home/nikolays/slurm_sim_ws/slurm_sim_tools/bin:$SLURM_SIM_DIR/bin:$SLURM_SIM_DIR/sbin:$PATH
#/usr/sbin/slurmctld
CLUS_DIR=`pwd`
slurmsim -v run_sim  \
            -s $SLURM_SIM_DIR \
            -e ${CLUS_DIR}/etc_sim \
            -a ${CLUS_DIR}/etc_sim/sacctmgr.script \
            -t ${CLUS_DIR}/etc_sim/workload.events \
            -r ${CLUS_DIR}/results/${MACHINE_NAME}/${RUN_NAME}/dtstart_${dtstart}_${replica} -d -v \
            -octld ${CLUS_DIR}/results/${MACHINE_NAME}/${RUN_NAME}/dtstart_${dtstart}_${replica}_ctld.out \
            -odbd ${CLUS_DIR}/results/${MACHINE_NAME}/${RUN_NAME}/dtstart_${dtstart}_${replica}_dbd.out \
            -dtstart $dtstart --no-slurmd >& ./results/${MACHINE_NAME}/${RUN_NAME}/dtstart_${dtstart}_${replica}.out


lolcow_latest.sif

singularity exec lolcow_latest.sif cowsay moo

ker run -it --rm alpine echo "\$HOSTNAME"
$HOSTNAME



singularity run docker://alpine echo "\$HOSTNAME"
p700

singularity instance.start --bind ${HOME} \
    --bind ${PWD}/mysql/var/lib/mysql/:/var/lib/mysql \
    --bind ${PWD}/mysql/run/mysqld:/run/mysqld \
    ./mysql.simg mysql

```