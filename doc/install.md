# Slurm Simulator

`slurm_sim_tools` is a repo for slurm simulator.
It includes necessary tools and `slurm_simulator` repo as a git-submodule

## Getting Source-Code

```bash
# create 
mkdir ~/slurm_sim_ws
cd ~/slurm_sim_ws

# --recursive is important to get slurm_simulator copy automatically
git clone --recursive https://github.com/ubccr-slurm-simulator/slurm_sim_tools.git
```

If you didn't use `--recursive` then you can get slurm_simulator manually:

```bash
git clone https://github.com/ubccr-slurm-simulator/slurm_sim_tools.git
cd slurm_sim_tool
git submodule update --init --recursive
```

# In source Installation <still relevant?>

Build cython
```bash
python setup.py build_ext --inplace
```
