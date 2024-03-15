# Slurm Simulator Docker and Apptainer Containers

```bash
docker build -f docker/slurm_sim/slurm_sim.Dockerfile -t nsimakov/slurm_sim:v3.0 .

# debug mode
# older docker uses --invoke
# BUILDX_EXPERIMENTAL=1 docker buildx build --invoke /bin/bash -f docker/slurm_sim/slurm_sim.Dockerfile -t nsimakov/slurm_sim:v3.0 .
BUILDX_EXPERIMENTAL=1 docker buildx debug build -f docker/slurm_sim/slurm_sim.Dockerfile -t nsimakov/slurm_sim:v3.0 .

# run
docker run -p 0.0.0.0:8888:8888 -it --rm \
    --name slurmsim -h slurmsim \
    -v $PWD/tutorials:/home/jovyan/work -v $PWD:/opt/slurm_sim_tools \
    -v /tmp/.X11-unix:/tmp/.X11-unix -v /mnt/wslg:/mnt/wslg \
    -e DISPLAY=$DISPLAY -e WAYLAND_DISPLAY=$WAYLAND_DISPLAY \
    -e XDG_RUNTIME_DIR=$XDG_RUNTIME_DIR -e PULSE_SERVER=$PULSE_SERVER \
    nsimakov/slurm_sim:v3.0

docker run -it -v /tmp/.X11-unix:/tmp/.X11-unix  \
    -e DISPLAY=$DISPLAY -e WAYLAND_DISPLAY=$WAYLAND_DISPLAY \
    -e XDG_RUNTIME_DIR=$XDG_RUNTIME_DIR -e PULSE_SERVER=$PULSE_SERVER xclock
    
docker run -p 0.0.0.0:8888:8888 -it --rm \
    --name slurmsim -h slurmsim \
    -v $PWD/tutorials:/home/jovyan/work -v $PWD:/opt/slurm_sim_tools \
    -v /tmp/.X11-unix:/tmp/.X11-unix -v /mnt/wslg:/mnt/wslg \
    -e DISPLAY=$DISPLAY -e WAYLAND_DISPLAY=$WAYLAND_DISPLAY \
    -e XDG_RUNTIME_DIR=$XDG_RUNTIME_DIR -e PULSE_SERVER=$PULSE_SERVER \
    -e NB_USER="slurm" \
    -e NB_UID="1000" \
    -e NB_GROUP="slurm" \
    -e NB_GID="1000" \
    -e CHOWN_HOME=yes \
    nsimakov/slurm_sim:v3.0 bash
    

```
Done running hooks in: /usr/local/bin/start-notebook.d
Update jovyan's UID:GID to 1000:100
Running hooks in: /usr/local/bin/before-notebook.d as uid: 0 gid: 0
Done running hooks in: /usr/local/bin/before-notebook.d


in container run following to set time:

```
Run 'dpkg-reconfigure tzdata' if you wish to change it.
```

# Slurm Simulator Docker and Singularity Containers v1.2

```bash
docker run -p 0.0.0.0:8888:8888 -it --rm -h slurmsim nsimakov/slurm_sim:v3.0

```

Building
## from repo root
docker build -f ./docker/slurm_sim/Dockerfile -t nsimakov/ub-slurm-sim:v1.2 .
docker push nsimakov/ub-slurm-sim:v1.2
Running


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