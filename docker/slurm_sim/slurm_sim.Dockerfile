# use jupyter/datascience-notebook:2024-02-13 x86_64-2023-10-20

FROM jupyter/datascience-notebook:x86_64-2023-10-20

LABEL desc="UB Slurm simulator"

USER root

# install build and run essential
RUN apt update && \
    apt install -y build-essential git sudo vim zstd libzstd-dev && \
    apt install -y munge libmunge-dev libhdf5-dev \
        libjwt-dev libyaml-dev libdbus-1-dev \
        libmariadb-dev mariadb-server mariadb-client && \
    apt install -y libssl-dev openssh-server openssh-client libssh-dev

# rename user:group to slurm:slurm
ARG NB_USER="slurm"
ARG NB_GROUP="slurm"
ARG NB_GID="1000"

ENV NB_USER="${NB_USER}" \
    NB_GROUP="${NB_GROUP}" \
    NB_GID=${NB_GID} \
    HOME="/home/${NB_USER}"

RUN usermod --login ${NB_USER} --move-home --home /home/${NB_USER} jovyan && \
    groupadd -g ${NB_GID} ${NB_GROUP} && \
    usermod -g ${NB_GROUP} ${NB_USER} && \
    usermod -a -G users ${NB_USER} && \
    usermod -a -G sudo ${NB_USER} &&  \
    echo "${NB_USER} ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers && \
    echo "${NB_USER}:slurm" |chpasswd && \
    fix-permissions "/home/${NB_USER}" && \
    chown -R ${NB_USER}:${NB_GROUP} /opt


# copy daemons starters
COPY ./docker/slurm_sim/cmd_start ./docker/slurm_sim/cmd_stop /usr/local/sbin/
# COPY ./docker/virtual_cluster/vctools /opt/cluster/vctools

# directories
RUN mkdir /scratch && chmod 777 /scratch && \
    mkdir /scratch/jobs && chmod 777 /scratch/jobs

# configure sshd
RUN mkdir /var/run/sshd && \
    echo 'root:root' |chpasswd && \
    echo 'PermitRootLogin yes' >> /etc/ssh/sshd_config

# setup munge,
RUN echo "secret munge key secret munge key secret munge key" >/etc/munge/munge.key &&\
    mkdir /run/munge  &&\
    chown -R slurm:slurm /var/log/munge /run/munge /var/lib/munge /etc/munge &&\
    chmod 600 /etc/munge/munge.key &&\
    su slurm -c "cmd_start munged" &&\
    munge -n | unmunge &&\
    su slurm -c "cmd_stop munged"

#configure mysqld
RUN cmd_start mysqld && \
    mysql -e 'DROP DATABASE IF EXISTS test;' && \
    mysql -e "CREATE USER 'slurm'@'%' IDENTIFIED BY 'slurm';" && \
    mysql -e 'GRANT ALL PRIVILEGES ON *.* TO "slurm"@"%" WITH GRANT OPTION;' && \
    mysql -e "CREATE USER 'slurm'@'localhost' IDENTIFIED BY 'slurm';" && \
    mysql -e 'GRANT ALL PRIVILEGES ON *.* TO "slurm"@"localhost" WITH GRANT OPTION;' && \
    cmd_stop mysqld

# set Slurm permissions, largely not needed for slurm sim
RUN mkdir /var/log/slurm  && \
    chown -R slurm:slurm /var/log/slurm  && \
    mkdir /var/state  && \
    chown -R slurm:slurm /var/state  && \
    mkdir -p /var/spool/slurmd  && \
    chown -R slurm:slurm /var/spool/slurmd && \
    touch /bin/mail  && chmod 755 /bin/mail

# more r and python dependencies
RUN fix-permissions "${CONDA_DIR}" && \
    mamba install --yes \
    'pymysql' 'qgrid'&& \
    mamba install --yes \
    'r-plotly' 'r-repr' 'r-irdisplay' 'r-pbdzmq' 'r-reticulate' 'r-cowplot' && \
    mamba clean --all -f -y && \
    fix-permissions "${CONDA_DIR}" && \
    fix-permissions "/home/${NB_USER}" && \
    jupyter labextension install @jupyter-widgets/jupyterlab-manager && \
    jupyter labextension install qgrid2

# Install eclipse for development porposes
RUN cd /tmp && \
    apt update && \
    apt install -y default-jre x11-apps libswt-gtk-4-jni && \
    wget https://mirror.umd.edu/eclipse/technology/epp/downloads/release/2023-12/R/eclipse-embedcpp-2023-12-R-linux-gtk-x86_64.tar.gz && \
    tar xf eclipse-embedcpp-2023-12-R-linux-gtk-x86_64.tar.gz -C /opt && \
    ln -s /opt/eclipse/eclipse /usr/local/bin/ && \
    rm eclipse-embedcpp-2023-12-R-linux-gtk-x86_64.tar.gz && \
    chown -R ${NB_USER}:${NB_GROUP} /opt/eclipse /usr/local/bin/eclipse

ARG DEBIAN_FRONTEND=noninteractive
EXPOSE  6080
EXPOSE  5900


#ARG RSTUDIO_VERSION
#ENV RSTUDIO_VERSION=${RSTUDIO_VERSION:-1.2.5042}
#ARG S6_VERSION
ARG PANDOC_TEMPLATES_VERSION
#ENV S6_VERSION=${S6_VERSION:-v1.21.7.0}
#ENV S6_BEHAVIOUR_IF_STAGE2_FAILS=2
ENV PATH=/usr/lib/rstudio-server/bin:$PATH
ENV PANDOC_TEMPLATES_VERSION=${PANDOC_TEMPLATES_VERSION:-2.9}

## Download and install RStudio server & dependencies
## Attempts to get detect latest version, otherwise falls back to version given in $VER
## Symlink pandoc, pandoc-citeproc so they are available system-wide

    #python-setuptools \
    #multiarch-support \
RUN apt-get update \
  && apt-get install -y --no-install-recommends \
    file \
    git \
    libapparmor1 \
    libclang-dev \
    libcurl4-openssl-dev \
    libedit2 \
    libssl-dev \
    lsb-release \
    psmisc \
    procps \
    sudo \
    wget \
  && wget -q "https://download2.rstudio.org/server/jammy/amd64/rstudio-server-2023.12.1-402-amd64.deb" \
  && dpkg -i rstudio-server-*-amd64.deb \
  && rm rstudio-server-*-amd64.deb \
  ## Symlink pandoc & standard pandoc templates for use system-wide
  ## && ln -s /usr/lib/rstudio-server/bin/pandoc/pandoc /usr/local/bin
#  && ln -s /usr/lib/rstudio-server/bin/pandoc/pandoc-citeproc /usr/local/bin \
#  && git clone --recursive --branch ${PANDOC_TEMPLATES_VERSION} https://github.com/jgm/pandoc-templates \
#  && mkdir -p /opt/pandoc/templates \
#  && cp -r pandoc-templates*/* /opt/pandoc/templates && rm -rf pandoc-templates* \
#  && mkdir /root/.pandoc && ln -s /opt/pandoc/templates /root/.pandoc/templates
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/ \
  ## RStudio wants an /etc/R, will populate from $R_HOME/etc
#  && mkdir -p /etc/R \
#  ## Write config files in $R_HOME/etc
#  && echo '\n\
#    \n# Configure httr to perform out-of-band authentication if HTTR_LOCALHOST \
#    \n# is not set since a redirect to localhost may not work depending upon \
#    \n# where this Docker container is running. \
#    \nif(is.na(Sys.getenv("HTTR_LOCALHOST", unset=NA))) { \
#    \n  options(httr_oob_default = TRUE) \
#    \n}' >> /usr/local/lib/R/etc/Rprofile.site \
#  && echo "PATH=${PATH}" >> /usr/local/lib/R/etc/Renviron \
#  ## Need to configure non-root user for RStudio
#  && useradd rstudio \
#  && echo "rstudio:rstudio" | chpasswd \
#	&& mkdir /home/rstudio \
#	&& chown rstudio:rstudio /home/rstudio \
#	&& addgroup rstudio staff \
#  ## Prevent rstudio from deciding to use /usr/bin/R if a user apt-get installs a package
#  &&  echo 'rsession-which-r=/usr/local/bin/R' >> /etc/rstudio/rserver.conf \
#  ## use more robust file locking to avoid errors when using shared volumes:
#  && echo 'lock-type=advisory' >> /etc/rstudio/file-locks \
#  ## configure git not to request password each time
#  && git config --system credential.helper 'cache --timeout=3600' \
#  && git config --system push.default simple \
#  ## Set up S6 init system
#  && wget -P /tmp/ https://github.com/just-containers/s6-overlay/releases/download/${S6_VERSION}/s6-overlay-amd64.tar.gz \
#  && tar xzf /tmp/s6-overlay-amd64.tar.gz -C / \
#  && mkdir -p /etc/services.d/rstudio
  && echo "#!/usr/bin/env bash" > /usr/local/bin/before-notebook.d/rstudio-run \
  && echo "exec /usr/lib/rstudio-server/bin/rserver" >> /usr/local/bin/before-notebook.d/rstudio-run \
  && chmod 755 /usr/local/bin/before-notebook.d/rstudio-run \
  # Server Configuration File
  && echo "rsession-which-r=/opt/conda/bin/R" >> /etc/rstudio/rserver.conf \
  && echo "auth-stay-signed-in-days=365" >> /etc/rstudio/rserver.conf \
  && echo "session-timeout-minutes=3000" >> /etc/rstudio/rserver.conf
#  && echo '#!/bin/bash \
#          \n rstudio-server stop' \
#          > /etc/services.d/rstudio/finish \
#  && mkdir -p /home/rstudio/.rstudio/monitored/user-settings \
#  && echo 'alwaysSaveHistory="0" \
#          \nloadRData="0" \
#          \nsaveAction="0"' \
#          > /home/rstudio/.rstudio/monitored/user-settings/user-settings \
#  && chown -R rstudio:rstudio /home/rstudio/.rstudio

#COPY userconf.sh /etc/cont-init.d/userconf
#
### running with "-e ADD=shiny" adds shiny server
#COPY add_shiny.sh /etc/cont-init.d/add
#COPY disable_auth_rserver.conf /etc/rstudio/disable_auth_rserver.conf
#COPY pam-helper.sh /usr/lib/rstudio-server/bin/pam-helper
#
EXPOSE 8787
#
### automatically link a shared volume for kitematic users
#VOLUME /home/rstudio/kitematic
#
#CMD ["/init"]

#USER ${NB_USER}
#WORKDIR "${HOME}"

RUN echo "#!/usr/bin/env bash" > /usr/local/bin/before-notebook.d/start-servises && \
    echo "/usr/local/sbin/cmd_start mysqld" >> /usr/local/bin/before-notebook.d/start-servises && \
    chmod 755 /usr/local/bin/before-notebook.d/start-servises

COPY --chown=${NB_USER}:${NB_GROUP} . /opt/slurm_sim_tools

# build optimized version
RUN mkdir -p /opt/slurm_sim_bld/slurm_sim_opt && \
    cd /opt/slurm_sim_bld/slurm_sim_opt && \
    /opt/slurm_sim_tools/slurm_simulator/configure --prefix=/opt/slurm_sim \
        --disable-x11 --enable-front-end \
        --with-hdf5=no \
        CFLAGS='-O3 -Wno-error=unused-variable -Wno-error=implicit-function-declaration' \
        --enable-simulator && \
    make -j 8 && \
    make -j 8 install && \
    mkdir -p /opt/slurm_sim_bld/slurm_sim_deb && \
    cd /opt/slurm_sim_bld/slurm_sim_deb && \
    /opt/slurm_sim_tools/slurm_simulator/configure --prefix=/opt/slurm_sim_deb \
        --disable-x11 --enable-front-end \
        --enable-developer --disable-optimizations --enable-debug \
        --with-hdf5=no \
       'CFLAGS=-g -O0 -Wno-error=unused-variable -Wno-error=implicit-function-declaration' \
       --enable-simulator && \
    make -j 8 && \
    make -j 8 install
# install R Slurm Simulator Toolkit
# install.packages("/home/slurm/slurm_sim_ws/slurm_sim_tools/src/RSlurmSimTools", repos = NULL, type="source")

ENV PATH="/opt/slurm_sim_tools/bin:$PATH" \
    PYTHONPATH="/opt/slurm_sim_tools/src:$PYTHONPATH"

# timezone is set to America/New_York change to your zone, tzdata is dependency of jupyterlab
#RUN sudo ln -fs /usr/share/zoneinfo/America/New_York /etc/localtime && \
#    echo "America/New_York" | sudo tee /etc/timezone && \
#    sudo DEBIAN_FRONTEND=noninteractive apt-get -y install tzdata

# python
#RUN  sudo apt install -y python3-pandas python3-jupyterlab-server jupyter \
#     python3-pip python3-arrow cython3 python3-pymysql python3-pytest python3-pytest-datadir \
#     python3-venv


#sudo DEBIAN_FRONTEND=noninteractive sudo apt install -y tzdata
# r

#sudo apt-get install r-base
#sudo apt-get install gdebi-core
#sudo gdebi rstudio-server-2023.12.1-402-amd64.deb
ARG DEBIAN_FRONTEND=noninteractive
USER root
