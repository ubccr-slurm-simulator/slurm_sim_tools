FROM centos:7

LABEL desc="Slurm simulator made ready"

#Adding in the code from github to be able to start/stop mysql (and sshd?)
COPY cmd_start /sbin/
COPY cmd_stop /sbin/


# giving permissions to use the cmd from above
RUN \
	chmod a+rwx /sbin/cmd_start && \
	chmod a+rwx /sbin/cmd_stop && \
        mkdir /install_files && \
        useradd -d /home/slurm -ms /bin/bash slurm && \
        usermod -aG wheel slurm && \
        echo "slurm:slurm"|chpasswd && \
        echo "Added slurm user" && \
	yum -y install git && \
	yum clean all

# getting file that installs all the R packages
COPY ./package_install.R /install_files

# creating all the directories needed for larger run command
USER slurm 
RUN \
        cd /home/slurm && \
        mkdir slurm_sim_ws && \
        cd slurm_sim_ws && \
        mkdir sim && \
        cd /home/slurm/slurm_sim_ws && \
        git clone https://github.com/ubccr-slurm-simulator/slurm_sim_tools.git

USER root


# installing mysql (mariadb), python, and R, setting everything up all in one Run command 
RUN \
	yum -y install mariadb-server && \
	yum -y install mariadb-devel && \
	echo "Done installing Mariadb" && \
	yum -y install gcc-c++ && \
	yum -y install install epel-release && \
	yum -y install python34 python34-libs python34-devel python34-numpy python34-scipy python34-pip && \
	pip3 install pymysql && \
	pip3 install pandas && \
	echo "Python all installed" && \
	yum -y install R R-Rcpp R-Rcpp-devel && \
	yum -y install python-devel && \
	yum -y install texlive-* && \
	echo "R all installed" && \
	Rscript /install_files/package_install.R && \
        echo "Installed R packages" && \
        yum -y install sudo && \
        yum -y install wget && \
	echo "Sudo, git, wget installed" && \
        wget https://download2.rstudio.org/rstudio-server-rhel-1.1.453-x86_64.rpm && \
        yum -y install rstudio-server-rhel-1.1.453-x86_64.rpm && \
        yum -y install initscripts && \
	echo "Rstudio server installed" && \
        yum -y install openssh openssh-server openssh-clients openssl-libs && \
        mkdir /var/run/sshd && \
        ssh-keygen -t rsa -f /etc/ssh/ssh_host_rsa_key -N '' && \
        ssh-keygen -t ecdsa -f /etc/ssh/ssh_host_ecdsa_key -N '' && \
        ssh-keygen -t ed25519 -f /etc/ssh/ssh_host_ed25519_key -N '' && \
	echo "Ssh installed" && \
        chmod g+rw /var/lib/mysql /var/log/mariadb /var/run/mariadb && \
        mysql_install_db && \
        chown -R mysql:mysql /var/lib/mysql && \
        cmd_start mysqld && \
        mysql -e "create user 'slurm'@'localhost' identified by 'slurm';" && \
        mysql -e "GRANT ALL PRIVILEGES ON *.* TO 'slurm'@'localhost' IDENTIFIED BY 'slurm';" && \
        cmd_stop mysqld && \
	yum clean all


# switch to slurm user so the next directories made are owned by slurm
USER slurm 

# installing slurm simulator
RUN \
	cd /home/slurm/slurm_sim_ws && \
        git clone https://github.com/ubccr-slurm-simulator/slurm_simulator.git && \
        cd slurm_simulator && \
        cd .. && \
        mkdir bld_opt && \
        cd bld_opt && \
        ../slurm_simulator/configure --prefix=/home/slurm/slurm_sim_ws/slurm_opt --enable-simulator \
--enable-pam --without-munge --enable-front-end --with-mysql-config=/usr/bin/ --disable-debug \
CFLAGS="-g -O3 -D NDEBUG=1" && \
        make -j install


# 8787 is the default port that rstudio server uses, so need to expose it to use it
EXPOSE 8787


USER root


COPY ./startup_file.sh /install_files
COPY ./initial_test.sh /install_files
COPY ./micro_cluster_setup.py /install_files
COPY ./micro_ws_config.sh /install_files
COPY ./populate_slurmdb.sh /install_files
COPY ./generate_job_trace.sh /install_files
COPY ./run_sim.sh /install_files
COPY ./check_results.R /install_files


# need to expose port 22 to allow for ssh to work properly
EXPOSE 22 


# expose for mysql use
EXPOSE 3306


# back to root for easier permissions stuff
RUN \
	chmod -R a+rwx /install_files


# sets cmd_start as entrypoint, then runs the startup file and the initial test file
ENTRYPOINT ["/sbin/cmd_start"]
CMD ["/install_files/startup_file.sh","/install_files/initial_test.sh"]


	
