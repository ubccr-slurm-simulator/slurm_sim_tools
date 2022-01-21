FROM centos:7

LABEL description="image to make slurm rpm"
USER root
# install dependencies
RUN \
    yum -y update && \
    yum -y install --setopt=tsflags=nodocs epel-release && \
    yum -y install --setopt=tsflags=nodocs \
        vim wget bzip2 \
        autoconf make gcc rpm-build \
        openssl openssh-clients openssl-devel \
        mariadb-server mariadb-devel \
        munge munge-devel \
        readline readline-devel \
        hdf5 hdf5-devel pam-devel hwloc hwloc-devel \
        perl perl-ExtUtils-MakeMaker python3

# source of slurm
ENV SLURM_TAR_BZ2_SOURCE=https://download.schedmd.com/slurm/slurm-21.08.4.tar.bz2

# volume for final rpms dump
VOLUME ./docker/virtual_cluster/RPMS

# setup entry point
WORKDIR /root

COPY ./docker/virtual_cluster/make_slurm_rpms_simsource ./docker/virtual_cluster/make_slurm_rpms ./docker/virtual_cluster/utils/cmd_setup ./docker/virtual_cluster/utils/cmd_start ./docker/virtual_cluster/utils/cmd_stop /usr/local/sbin/
ENTRYPOINT ["/usr/local/sbin/cmd_start"]
CMD ["make_slurm_rpms"]
