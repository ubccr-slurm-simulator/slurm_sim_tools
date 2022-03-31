FROM centos:7

LABEL description="slurm sim node"
USER root
# setup entry point
WORKDIR /root

############################
# building dep
# install dependencies
RUN \
    yum -y update && \
    yum -y install --setopt=tsflags=nodocs epel-release && \
    yum -y install --setopt=tsflags=nodocs \
        vim wget bzip2 \
        autoconf make gcc rpm-build \
        gdb gdb-gdbserver \
        openssl openssh-clients openssl-devel \
        mariadb-server mariadb-devel \
        munge munge-devel \
        readline readline-devel \
        hdf5 hdf5-devel pam-devel hwloc hwloc-devel \
        perl perl-ExtUtils-MakeMaker python3

############################
# Common

# install dependencies
RUN \
    yum update --assumeno || true && \
    yum -y install --setopt=tsflags=nodocs epel-release && \
    yum -y install --setopt=tsflags=nodocs \
        openssl openssh-server openssh-clients \
        munge sudo && \
    yum clean all && \
    rm -rf /var/cache/yum
#        vim tmux mc perl-Switch\
#        iproute \
#        perl-Date* \
#        gcc-c++ python3 \
WORKDIR /root

# copy daemons starters
COPY ./docker/virtual_cluster/utils/cmd_setup ./docker/virtual_cluster/utils/cmd_start ./docker/virtual_cluster/utils/cmd_stop /usr/local/sbin/
COPY ./docker/virtual_cluster/vctools /opt/cluster/vctools
# directories
RUN mkdir /scratch && chmod 777 /scratch && \
    mkdir /scratch/jobs && chmod 777 /scratch/jobs

# add users
RUN useradd -m -s /bin/bash slurm && \
    echo 'slurm:slurm' |chpasswd && \
    usermod -a -G wheel slurm && \
    echo "slurm ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers

# configure sshd
RUN mkdir /var/run/sshd && \
    ssh-keygen -t rsa -f /etc/ssh/ssh_host_rsa_key -N '' && \
    ssh-keygen -t ecdsa -f /etc/ssh/ssh_host_ecdsa_key -N '' && \
    ssh-keygen -t ed25519 -f /etc/ssh/ssh_host_ed25519_key -N '' && \
    echo 'root:root' |chpasswd && \
    echo 'PermitRootLogin yes' >> /etc/ssh/sshd_config
# uncomment two previous line if there is a need for root access through ssh

# setup munge
RUN echo "secret munge key secret munge key secret munge key" >/etc/munge/munge.key &&\
    chown -R munge:munge /var/log/munge /run/munge /var/lib/munge /etc/munge &&\
    chmod 600 /etc/munge/munge.key &&\
    cmd_start munged &&\
    munge -n | unmunge &&\
    cmd_stop munged

EXPOSE 22

# install miniapps
COPY ./docker/virtual_cluster/apps/microapps /opt/cluster/microapps
# RUN cd /usr/local/miniapps && make

# edit system processor limits
RUN sudo echo -e "# Default limit for number of user's processes to prevent \n \
 *          \soft    nproc     unlimited \n root       soft    nproc     unlimited" \
> /etc/security/limits.d/20-nproc.conf

# setup entry point
ENTRYPOINT ["/usr/local/sbin/cmd_start"]
CMD ["sshd", "bash"]

############################
# Headnode
# install dependencies
RUN yum update --assumeno || true && \
    yum -y install --setopt=tsflags=nodocs \
        vim tmux mc perl-Switch \
        iproute perl-Date* \
        mariadb-server python3 python36-PyMySQL python36-psutil \
        sudo perl-Date* zstd && \
    pip3 install pandas py-cpuinfo tqdm gdbgui && \
    yum clean all && \
    rm -rf /var/cache/yum

#configure mysqld
RUN chmod g+rw /var/lib/mysql /var/log/mariadb /var/run/mariadb && \
    mysql_install_db && \
    chown -R mysql:mysql /var/lib/mysql && \
    cmd_start mysqld && \
    mysql -e 'DELETE FROM mysql.user WHERE user NOT LIKE "root";' && \
    mysql -e 'DELETE FROM mysql.user WHERE Host NOT IN ("localhost","127.0.0.1","%");' && \
    mysql -e 'GRANT ALL PRIVILEGES ON *.* TO "root"@"%" WITH GRANT OPTION;' && \
    mysql -e 'GRANT ALL PRIVILEGES ON *.* TO "root"@"localhost" WITH GRANT OPTION;' && \
    mysql -e 'DROP DATABASE IF EXISTS test;' && \
    mysql -e "CREATE USER 'slurm'@'%' IDENTIFIED BY 'slurm';" && \
    mysql -e 'GRANT ALL PRIVILEGES ON *.* TO "slurm"@"%" WITH GRANT OPTION;' && \
    mysql -e "CREATE USER 'slurm'@'localhost' IDENTIFIED BY 'slurm';" && \
    mysql -e 'GRANT ALL PRIVILEGES ON *.* TO "slurm"@"localhost" WITH GRANT OPTION;' && \
    cmd_stop mysqld

COPY ./src ./bin ./docker /opt/cluster/slurm_sim_tools/



EXPOSE 6819
EXPOSE 6817

#install Slurm permissions
RUN mkdir /var/log/slurm  && \
    chown -R slurm:slurm /var/log/slurm  && \
    mkdir /var/state  && \
    chown -R slurm:slurm /var/state  && \
    mkdir -p /var/spool/slurmd  && \
    chown -R slurm:slurm /var/spool/slurmd && \
    touch /bin/mail  && chmod 755 /bin/mail && \
    echo '/opt/cluster/vctools/start_head_node.sh' >> /root/.bash_history

############################
# Build Slurm Sim
#install Slurm
COPY slurm_simulator /opt/cluster/slurm_sim_tools/slurm_simulator
RUN mkdir /root/bld && cd /root/bld && \
    /opt/cluster/slurm_sim_tools/slurm_simulator/configure --prefix=/usr  --sysconfdir=/etc/slurm --disable-x11 --with-hdf5=no --enable-simulator --enable-front-end --disable-optimizations --enable-debug CFLAGS="-g -O0" && \
    make -j && \
    make -j install
EXPOSE 5000
# setup entry point
ENTRYPOINT ["/usr/local/sbin/cmd_start"]
CMD ["sshd", "munged", "mysqld", "/opt/cluster/vctools/add_system_users.sh", "bash"]
