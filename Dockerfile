##############################################################################
### Builder Image
##
#
# Will install the following software in /opt :
# - minio client binary
# - cqlsh from source using pipx
# - our application from source using pipx
FROM python:3.12-bullseye AS python-builder


###############################################################################
## Arguments
#
# URL for downloading the minio client binary
ARG mc_bin_url="https://dl.min.io/client/mc/release/linux-amd64/archive/mc.RELEASE.2024-01-28T16-23-14Z"
# git repository to clone to get cqlsh source
ARG cqlsh_repository=https://github.com/youwol-jdecharne/scylla-cqlsh.git
# git commitish to checkout for cqlsh source
ARG cqlsh_tag=v6.0.7-youwol
# gcc version for apt package
ARG gcc_version=4:10.2.1-1
# git version for apt packagae
ARG git_version=1:2.30.2-1+deb11u2
# pip version for pypi
ARG pip_version=23.1.2
# pipx version for pypi
ARG pipx_version=1.2.0
# Does not matter that much, just hold the downloaded sources for installation
WORKDIR /usr/src/apps


###############################################################################
## OS-level dependencies
#
# Prevent some packages from prompting interactive input
ENV DEBIAN_FRONTEND=noninteractive
# * Update & install dependencies with the package manager
#   - git : clone cqlsh repository
#   - gcc : for cqlsh cythonication
# * Update pip to the latest
# * pipx is not available in bullseye, install it with pip
RUN    apt-get update \
    && apt-get install \
       --no-install-recommends \
       --allow-downgrades \
       --assume-yes \
       gcc="$gcc_version" \
       git="$git_version" \
    && apt-get clean \
    && pip install \
       pip=="$pip_version" \
       pipx=="$pipx_version"
# pipx venvs & apps directories in /opt
ENV PIPX_HOME=/opt/pipx/home
ENV PIPX_BIN_DIR=/opt/pipx/bin


###############################################################################
## Minio client & Cqlsh
#
# * Bin directory in /opt
# * Download minio-client binary in /opt/minio-client/bin
#     and set executable permissions
# * Get cqlsh the source from repository
#     and install it with pipx
RUN    mkdir -p /opt/minio-client/bin \
    && curl "$mc_bin_url" \
       -o /opt/minio-client/bin/mc \
    && chmod a+x /opt/minio-client/bin/mc \
    && git clone --depth 1 \
       --branch "$cqlsh_tag" \
       "$cqlsh_repository" cqlsh \
    && pipx install ./cqlsh


###############################################################################
## Our application
#
# Get the source from build context
COPY . cluster-data-manager
# Install with pipx from source
RUN pipx install ./cluster-data-manager



###############################################################################
### Final image
##
#
# - create user data-manager
# - set up application environment variables
# - create working directories & define VOLUME
# - copy installed softwares from builder image
# - define ENTRYPOINT
FROM python:3.12-slim AS final


###############################################################################
## Arguments
#
# the root working directory path & VOLUME
ARG path_work_dir=/var/opt/data-manager
# the HOME dirctory for data-manager
ARG path_data_manager_home=/opt/data-manager

###############################################################################
## Create user data-manager
#
# Create user & user home directory
RUN useradd \
    --home-dir "$path_data_manager_home" \
    --create-home \
    --uid 1000 \
    data-manager
# Use user HOME as the image WORKDIR
WORKDIR $path_data_manager_home


###############################################################################
## Environment variables for our application
#
# Binaries paths
ENV PATH=/opt/pipx/bin:$PATH
ENV PATH_MINIO_CLIENT=/opt/minio-client/bin/mc
ENV CQLSH_COMMAND=/opt/pipx/bin/cqlsh
# Working directories paths
ENV PATH_WORK_DIR=$path_work_dir
ENV PATH_LOG_FILE=$PATH_WORK_DIR/entry_point.log
ENV PATH_KEYCLOAK_STATUS_FILE=$PATH_WORK_DIR/kc/kc_status
ENV PATH_KEYCLOAK_COMMON_SCRIPT=$PATH_WORK_DIR/kc/kc_common.sh
ENV PATH_KEYCLOAK_SCRIPT=$PATH_WORK_DIR/kc/kc_script.sh
# configuration directory for minio client
ENV PATH_MINIO_CLIENT_CONFIG=$path_data_manager_home/.mc


###############################################################################
## Create application working directories
#
# Our working directory
RUN mkdir -p "$PATH_WORK_DIR" && \
    chown -R data-manager "$PATH_WORK_DIR"
# Define the image VOLUME
VOLUME $path_work_dir


###############################################################################
## Copy previously installed softwares
#
COPY --from=python-builder /opt /opt


###############################################################################
## Image entry point
#
# Run as user data-manager
USER 1000
# Start our script, from pipx installation
ENTRYPOINT ["data-manager"]
