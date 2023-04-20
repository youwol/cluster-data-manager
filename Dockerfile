#######################
## Builder Image
#  image to build cqlsh (COPY commands optimized with cython) and install minio client
FROM python:3.11-bullseye AS python-builder

# Does not matter that much, everything will be installed in /opt/venv
WORKDIR /usr/src/apps

# Install OS-level dependencies
RUN apt-get update && apt-get install --assume-yes git gcc

# Download minio-client binary
ARG mc_bin_url="https://dl.min.io/client/mc/release/linux-amd64/mc"
RUN mkdir -p /opt/minio-client/bin && \
    mkdir -p /opt/minio-client/config && \
    curl "$mc_bin_url" -o /opt/minio-client/bin/mc && \
    chmod a+x /opt/minio-client/bin/mc

# Create a virtual environment and use it
RUN python -m venv /opt/venv
ENV PATH=/opt/venv/bin:$PATH
RUN pip install --upgrade pip

# Install cqlsh from sources
ARG cqlsh_repository=https://github.com/youwol-jdecharne/scylla-cqlsh.git
ARG cqlsh_tag=v6.0.7-youwol
RUN git clone $cqlsh_repository cqlsh
RUN git -C cqlsh checkout $cqlsh_tag
RUN pip install cqlsh/

# Install our app’s python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

##############
## Final image
#
FROM python:3.11-slim
# Copy previously setup venv (should have the same path ?) and use it
COPY --from=python-builder /opt/venv /opt/venv
ENV PATH=/opt/venv/bin:$PATH

# Copy previously downloaded minio-client
COPY --from=python-builder /opt/minio-client /opt/minio-client

RUN useradd -m -d /opt/app data-manager


# Our application directory
WORKDIR /opt/app

# Our work dir
RUN mkdir -p /var/tmp/app
RUN chown -R data-manager /var/tmp/app
RUN chown -R data-manager /opt/minio-client/config
VOLUME ["/var/tmp/app"]

# Copy our application sources
COPY src /opt/app

# Environment for our application
ENV PATH_MINIO_CLIENT="/opt/minio-client/bin/mc"
ENV PATH_MINIO_CLIENT_CONFIG="/opt/minio-client/config"
ENV CQLSH_COMMAND="/opt/venv/bin/cqlsh"
ENV PATH_LOG_FILE="/var/tmp/app/entry_point.log"
ENV PATH_WORK_DIR="/var/tmp/app"

USER data-manager
# Start our script
# - python is taken from /opt/venv/bin (see ENV PATH above)
# - entry_point.py is in /opt/app (see WORKDIR above)
ENTRYPOINT ["python", "entry_point.py"]
