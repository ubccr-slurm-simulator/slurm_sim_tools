FROM centos:7

LABEL desc="Slurm simulator made ready"

#Adding in the code from github to be able to start/stop mysql (and sshd?)
COPY cmd_start /sbin/
COPY cmd_stop /sbin/

# giving permissions to use the cmd from above
RUN \
	chmod a+rwx /sbin/cmd_start && \
	chmod a+rwx /sbin/cmd_stop

# installing mysql (mariadb)
RUN \
	yum -y update && \
	yum -y install mariadb-server && \
	yum -y install mariadb-devel && \
	echo "Done installing Mariadb"


#Python (need to install gcc-c++ to get the gcc command to work down the road with pandas
RUN \
	yum -y install gcc-c++ && \
	yum -y install install epel-release && \
	yum -y install python34 python34-libs python34-devel python34-numpy python34-scipy python34-pip && \
	pip3 install pymysql && \
	pip3 install pandas && \
	echo "Python all installed"



#Installing R
RUN \
	yum -y install R R-Rcpp R-Rcpp-devel && \
	yum -y install python-devel && \
	yum -y install texlive-* && \
	echo "R all installed"

# Installing some additional things to do things down the line
# sudo - to allow slurm to give root commands if needed
# git - to get stuff from github
# wget - to be able to get rstudio server on the machine
# Adding the slurm user to the system - need to install sudo for sudo commands..?
RUN \
	yum -y install sudo && \
	yum -y install git && \
	yum -y install wget

# setting up directories and adding slurm user
RUN \
	mkdir /install_files && \
	useradd -d /home/slurm -ms /bin/bash slurm && \
	usermod -aG wheel slurm && \
	echo "slurm:slurm"|chpasswd && \
	echo "Added slurm user"

# switch to slurm user so the next directories made are owned by slurm
USER slurm 

# making the directory for slurm simulations, the install files (R script) and installing toolkit
RUN \
	cd /home/slurm && \
	mkdir slurm_sim_ws && \
	cd slurm_sim_ws && \
	mkdir sim && \
	cd /home/slurm/slurm_sim_ws && \
	git clone https://github.com/nsimakov/slurm_sim_tools.git

# switch back to root user so can have all access needed
USER root

# copies over the R script that installs all the packages for R into the installFiles in the root directory
COPY ./package_install.R /install_files

#Runs the R script to install the packages
RUN \
	Rscript /install_files/package_install.R && \
	echo "Installed packages"

#This installs Rstudio Server
RUN \
	wget https://download2.rstudio.org/rstudio-server-rhel-1.1.453-x86_64.rpm && \
	yum -y install rstudio-server-rhel-1.1.453-x86_64.rpm && \
	yum -y install initscripts

# 8787 is the default port that rstudio server uses, so need to expose it to use it
EXPOSE 8787

# installs ssh and makes some keys for it
RUN \
	yum -y install openssh openssh-server openssh-clients openssl-libs && \
	mkdir /var/run/sshd && \
	ssh-keygen -t rsa -f /etc/ssh/ssh_host_rsa_key -N '' && \
	ssh-keygen -t ecdsa -f /etc/ssh/ssh_host_ecdsa_key -N '' && \
	ssh-keygen -t ed25519 -f /etc/ssh/ssh_host_ed25519_key -N ''	

# need to expose port 22 to allow for ssh to work properly
EXPOSE 22 

# configuring mysqld (get it up and running and add the slurm user)
RUN \
	chmod g+rw /var/lib/mysql /var/log/mariadb /var/run/mariadb && \
    	mysql_install_db && \
    	chown -R mysql:mysql /var/lib/mysql && \
	cmd_start mysqld && \
	mysql -e "create user 'slurm'@'localhost' identified by 'slurm';" && \
	mysql -e "GRANT ALL PRIVILEGES ON *.* TO 'slurm'@'localhost' IDENTIFIED BY 'slurm';" && \
	cmd_stop mysqld 

# expose for mysql use
EXPOSE 3306

# slurm user switch again
USER slurm

# installing the slurm simulator from github - making appropriate directories as well
RUN \
	cd /home/slurm/slurm_sim_ws && \
	git clone https://github.com/nsimakov/slurm_simulator.git && \
	cd slurm_simulator && \
	cd .. && \
	mkdir bld_opt && \
	cd bld_opt && \
	../slurm_simulator/configure --prefix=/home/slurm/slurm_sim_ws/slurm_opt --enable-simulator \
--enable-pam --without-munge --enable-front-end --with-mysql-config=/usr/bin/ --disable-debug \
CFLAGS="-g -O3 -D NDEBUG=1" && \
	make -j install

# back to root for easier permissions stuff
USER root

# copies over files used in startup
COPY ./startup_file.sh /install_files  
COPY ./initial_test.sh /install_files
COPY ./micro_cluster_setup.py /install_files
COPY ./micro_ws_config.sh /install_files
COPY ./populate_slurmdb.sh /install_files
COPY ./generate_job_trace.sh /install_files
COPY ./run_sim.sh /install_files
COPY ./check_results.R /install_files


# give rwx permissions of install_files directory to everyone so can run things
RUN \
	chmod -R a+rwx /install_files



# need to expose this for the slurmdbd to work maybe?
#EXPOSE 29001 
 

# sets cmd_start as entrypoint, then runs the startup file and the initial test file
ENTRYPOINT ["/sbin/cmd_start"]
CMD ["/install_files/startup_file.sh","/install_files/initial_test.sh"]


	
