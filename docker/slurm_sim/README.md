# Slurm Simulator Docker and Singularity Containers

```bash
docker build -f docker/virtual_cluster/Common.Dockerfile -t nsimakov/slurm_common:1 .
```

Building
# from repo root
docker build -f ./docker/slurm_sim/Dockerfile -t nsimakov/ub-slurm-sim:v1.2 .
docker push nsimakov/ub-slurm-sim:v1.2
Running