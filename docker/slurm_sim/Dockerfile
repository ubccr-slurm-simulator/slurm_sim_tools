FROM centos:7

LABEL desc="Slurm simulator"

# installing mysql (mariadb), utils, openssl and texlive
RUN yum -y update && \
	yum -y install install epel-release && \
	yum -y install sudo wget mc git gcc-c++ && \
	echo "Done with utils" && \
	yum -y install mariadb-server && \
	yum -y install mariadb-devel && \
	echo "Done installing Mariadb" && \
	yum -y install texlive-* && \
	echo "texlive installed" && \
	yum -y install openssh openssh-server openssh-clients openssl-libs && \
	echo "openssh installed"

# python
RUN	yum -y install python36 python36-libs python36-devel python36-numpy python36-scipy python36-pip && \
	pip3 install pymysql && \
	pip3 install pandas && \
	echo "Python installed"

# R
COPY docker/slurm_sim/install_packages.R /root/
RUN yum -y update && \
    yum -y install R R-Rcpp R-Rcpp-devel && \
    mkdir -p /usr/share/doc/R-3.6.0/html && \
    cp /usr/lib64/R/library/stats/html/R.css /usr/share/doc/R-3.6.0/html/ && \
    wget https://download2.rstudio.org/server/centos7/x86_64/rstudio-server-rhel-1.4.1103-x86_64.rpm && \
    yum -y install rstudio-server-rhel-1.4.1103-x86_64.rpm && \
    yum -y install initscripts && \
    Rscript /root/install_packages.R && \
	echo "R all installed"

# 8787 is the default port that rstudio server uses, so need to expose it to use it
EXPOSE 8787
# need to expose port 22 to allow for ssh to work properly
EXPOSE 22
# expose for mysql use
EXPOSE 3306

COPY docker/utils/cmd_start docker/utils/cmd_stop docker/utils/cmd_setup /usr/local/bin/

# setup
RUN useradd -d /home/slurm -ms /bin/bash slurm && \
    echo "slurm:slurm"|chpasswd && \
    usermod -a -G wheel slurm && \
    echo "slurm ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers && \
    echo "Added slurm user" && \
    mkdir -p /home/slurm/slurm_sim_ws/sim && \
    chown -R slurm:slurm /home/slurm/slurm_sim_ws && \
    \
    mkdir /var/run/sshd && \
    ssh-keygen -t rsa -f /etc/ssh/ssh_host_rsa_key -N '' && \
    ssh-keygen -t ecdsa -f /etc/ssh/ssh_host_ecdsa_key -N '' && \
    ssh-keygen -t ed25519 -f /etc/ssh/ssh_host_ed25519_key -N '' && \
	echo "Ssh set" && \
	\
	chmod g+rw /var/lib/mysql /var/log/mariadb /var/run/mariadb && \
    mysql_install_db && \
    chown -R mysql:mysql /var/lib/mysql && \
    cmd_start mysqld && \
    mysql -e "create user 'slurm'@'localhost' identified by 'slurm';" && \
    mysql -e "GRANT ALL PRIVILEGES ON *.* TO 'slurm'@'localhost' IDENTIFIED BY 'slurm';" && \
    cmd_stop mysqld && \
    echo "sqldb set"

# switch to slurm user so the next directories made are owned by slurm
USER slurm
WORKDIR /home/slurm
# instal slurm simulator
COPY --chown=slurm:slurm slurm-simulator /home/slurm/slurm_sim_ws/slurm_sim_tools/
RUN \
	cd /home/slurm/slurm_sim_ws && \
    git clone  --depth 1 --branch slurm-17-11_Sim https://github.com/ubccr-slurm-simulator/slurm_simulator.git && \
    mkdir -p bld/opt && \
    cd bld/opt && \
    ../../slurm_simulator/configure --prefix=/home/slurm/slurm_sim_ws/slurm_opt --enable-simulator \
--enable-pam --without-munge --enable-front-end --with-mysql-config=/usr/bin/ --disable-debug \
CFLAGS="-g -O3 -D NDEBUG=1" && \
    make -j install

COPY --chown=slurm:slurm doc src tutorials README.md /home/slurm/slurm_sim_ws/slurm_sim_tools/

# instal RSlurmSimTools
RUN rm -rf /home/slurm/slurm_sim_ws/slurm_sim_tools/.idea && \
    sudo Rscript /home/slurm/slurm_sim_ws/slurm_sim_tools/docker/slurm_sim/install_rslurmsimtools.R

# sets cmd_start as entrypoint, then runs the startup file and the initial test file
ENTRYPOINT ["/home/slurm/slurm_sim_ws/slurm_sim_tools/docker/slurm_sim/startup.sh"]
