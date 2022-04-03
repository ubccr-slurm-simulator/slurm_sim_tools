# Slurm Simulator Docker and Singularity Containers

```bash
docker build -f docker/virtual_cluster/Common.Dockerfile -t nsimakov/slurm_common:1 .
```

Building
# from repo root
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