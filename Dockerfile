#######################
## Builder Image
#  image to build cqlsh (COPY commands optimized with cython), install minio client and install our application
FROM python:3.11-bullseye AS python-builder

# Does not matter that much, just hold the downloaded sources for installation
WORKDIR /usr/src/apps

# Install OS-level dependencies
RUN apt-get update && apt-get install --assume-yes git gcc
RUN pip install --upgrade pip

# Download minio-client binary
ARG mc_bin_url="https://dl.min.io/client/mc/release/linux-amd64/mc"
RUN mkdir -p /opt/minio-client/bin && \
    mkdir -p /opt/minio-client/config && \
    curl "$mc_bin_url" -o /opt/minio-client/bin/mc && \
    chmod a+x /opt/minio-client/bin/mc

# Install pipx
ENV PIPX_HOME=/opt/pipx/home
ENV PIPX_BIN_DIR=/opt/pipx/bin
RUN pip install pipx

# Install cqlsh from sources
ARG cqlsh_repository=https://github.com/youwol-jdecharne/scylla-cqlsh.git
ARG cqlsh_tag=v6.0.7-youwol
RUN git clone $cqlsh_repository cqlsh
RUN git -C cqlsh checkout $cqlsh_tag
RUN pipx install ./cqlsh

# Install our app
COPY . cluster-data-manager
RUN pipx install ./cluster-data-manager

##############
## Final image
#
FROM python:3.11-slim
# Copy previously downloaded minio-client
COPY --from=python-builder /opt/minio-client /opt/minio-client

# Copy previously pipx intallations (must have the same path) and use it
COPY --from=python-builder /opt/pipx /opt/pipx
ENV PATH=/opt/pipx/bin:$PATH

# Create user
RUN useradd -m -d /opt/app data-manager
WORKDIR /opt/app

# Our working directories
RUN mkdir -p /var/tmp/app
RUN chown -R data-manager /var/tmp/app
RUN chown -R data-manager /opt/minio-client/config
VOLUME ["/var/tmp/app"]

# Environment for our application
ENV PATH_MINIO_CLIENT="/opt/minio-client/bin/mc"
ENV PATH_MINIO_CLIENT_CONFIG="/opt/minio-client/config"
ENV CQLSH_COMMAND="/opt/pipx/bin/cqlsh"
ENV PATH_LOG_FILE="/var/tmp/app/entry_point.log"
ENV PATH_WORK_DIR="/var/tmp/app"

USER data-manager
# Start our script, installed by pipx
ENTRYPOINT ["data-manager"]
