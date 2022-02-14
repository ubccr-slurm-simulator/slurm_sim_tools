FROM nsimakov/slurm_common:1

LABEL description="Compute Node Image for Slurm Virtual Cluster"

USER root

# copy slurm rpm
COPY ./docker/virtual_cluster/RPMS/x86_64/slurm-21.08.4-1.el7.x86_64.rpm ./docker/virtual_cluster/RPMS/x86_64/slurm-slurmd-21.08.4-1.el7.x86_64.rpm /root/
#/docker/virtual_cluster/RPMS/x86_64/slurm-perlapi-*.x86_64.rpm ./docker/virtual_cluster/RPMS/x86_64/slurm-pam_slurm-*.x86_64.rpm
#COPY ./micro1/bin/slurm-epilog /usr/local/bin/slurm-epilog
#COPY ./micro1/bin/slurm-prolog /usr/local/bin/slurm-prolog
COPY ./docker/virtual_cluster/password-auth /etc/pam.d/password-auth

#install Slurm
RUN ls && yum update --assumeno || true && \
    yum -y install \
        slurm-[0-9]*.x86_64.rpm \
        slurm-slurmd-*.x86_64.rpm \
        && \
    rm slurm*.rpm  && \
    mkdir /var/log/slurm  && \
    chown -R slurm:slurm /var/log/slurm  && \
    mkdir /var/state  && \
    chown -R slurm:slurm /var/state  && \
    mkdir -p /var/spool/slurmd  && \
    chown -R slurm:slurm /var/spool/slurmd && \
    yum clean all && \
    rm -rf /var/cache/yum
# slurm-pam_slurm-*.x86_64.rpm   slurm-perlapi-*.x86_64.rpm
EXPOSE 6818

# setup entry point
ENTRYPOINT ["/usr/local/sbin/cmd_start"]
CMD ["-loop", "/opt/cluster/vctools/init_system", "munged", "slurmd", "sshd", "/opt/cluster/vctools/init_slurm", "bash"]
