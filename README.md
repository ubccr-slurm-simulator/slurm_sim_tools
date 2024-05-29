---
editor_options: 
  markdown: 
    wrap: 72
---

## Slurm Simulator

Center for Computational Research, University at Buffalo, SUNY

## News

-   05/30/2024. The new version (v3.0) of Slurm Simulation is out. It is
    based on Slurm 23.02. The goal of the new version is to be
    sufficiently faster and reasonably accurate. See Figure 1 for
    comparison of Slurm simulator results with unmodified Slurm run.
    -   To run Slurm Simulator user docker container [nsimakov/slurm_sim:v3.0](https://hub.docker.com/repository/docker/nsimakov/slurm_sim/general).
    -   See [tutorials](tutorials/) on how to run it.
    -   Use
        [v3.0-branch](https://github.com/ubccr-slurm-simulator/slurm_sim_tools/tree/v3.0-branch)
        for the toolkit and [slurm-23-02-sim
        branch](https://github.com/ubccr-slurm-simulator/slurm_simulator/tree/slurm-23-02-sim)
        for Slurm simulator. Use

## Overview

Slurm is an open source job scheduling system that is widely used in
many small and large-scale HPC resources, including almost all current
XSEDE resources. Like all resource management programs, Slurm is highly
tunable, with many parametric settings that can significantly influence
job throughput, overall system utilization and job wait times.
Unfortunately, in many cases it is difficult to judge how modification
of these parameters will affect the overall performance of the HPC
resource. For example, a given policy choice which changes a single
Slurm parameter may have unintended and perhaps undesirable consequences
for the overall performance of the HPC system. Also, it may take days or
even weeks to see what, if any, impact certain changes have on the
scheduler performance and operation. For these reasons, attempting to
tune system performance or implement new policy choices through changes
in the Slurm parameters on a production HPC system is not practical. In
a real sense, HPC center personnel are often times operating in the dark
with respect to tuning the Slurm parameter space to optimize job
throughput or resource efficiency. The ability to simulate a Slurm
operating environment can therefore provide a means to improve an
existing production system or predict the performance of a newly planned
HPC system, without impacting the production instance of Slurm

We have developed a standalone Slurm Simulator, which runs on a
workstation or a single HPC node, that allows time accelerated
simulation of workloads on HPC resources. Based on a modification of the
actual Slurm code, the simulator can be used to study the effects of
different Slurm parameters on HPC resource performance and to optimize
these parameters to fit a particular need or policy, for example,
maximizing throughput for a particular range of job sizes. In the
current implementation, the Slurm simulator can model historic or
synthetic workloads of a single cluster. For small clusters, the
simulator can simulate as many as 17 days per hour depending on the job
composition, and the Slurm configuration.

![**Figure 1.** Mean over independent runs of mean wait-time. Virtual
Cluster is an unmodified Slurm installation on Docker containers where
each node (head and compute) is represented by a separate Docker
container.](doc/images/mean_mean_wait_time.png){width="4in"}

Toolkit and documentation for Slurm simulator repository:

> <https://github.com/nsimakov/slurm_sim_tools>

Slurm simulator repository:

> <https://github.com/nsimakov/slurm_simulator>

Publications:

1.  N.A. Simakov, R.L. DeLeon, M.D. Innus, M.D. Jones, J.P. White, S.M.
    Gallo, A.K. Patra, and T.R. Furlani. (2018) A Slurm Simulator:
    Implementation and Parametric Analysis. In: Jarvis S., Wright S.,
    Hammond S. (eds) High Performance Computing Systems. Performance
    Modeling, Benchmarking, and Simulation. PMBS 2017. Lecture Notes in
    Computer Science, vol 10724. Springer, Cham.
    <https://link.springer.com/chapter/10.1007/978-3-319-72971-8_10>

2.  N.A. Simakov, R.L. DeLeon, M.D. Innus, M.D. Jones, J.P. White, S.M.
    Gallo, A.K. Patra, and T.R. Furlani. 2018. Slurm Simulator:
    Improving Slurm Scheduler Performance on Large HPC systems by
    Utilization of Multiple Controllers and Node Sharing. In Proceedings
    of the Practice and Experience on Advanced Research Computing (PEARC
    '18). ACM, New York, NY, USA, Article 25, 8 pages. DOI:
    <https://doi.org/10.1145/3219104.3219111>
