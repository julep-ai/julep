FROM ubuntu:jammy

# Install dependencies
RUN \
    apt-get update -yqq && \
    apt-get install -y ca-certificates tini nfs-common nfs-kernel-server netcat procps netbase && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Set fallback mount directory
ENV MNT_DIR /home/cozo

# Copy local code to the container image.
ENV APP_HOME /app
WORKDIR $APP_HOME
COPY ./bin ./bin
COPY ./run.sh ./run.sh

ENV COZO_AUTH_TOKEN ""
ENV COZO_ROCKSDB_FILE "cozo.db"

# Ensure the script is executable
RUN \
    mkdir -p $MNT_DIR && \
    chmod +x /app/bin/cozo-bin && \
    chmod +x /app/run.sh

# Use tini to manage zombie processes and signal forwarding
# https://github.com/krallin/tini
ENTRYPOINT ["/usr/bin/tini", "--"]

# Pass the startup script as arguments to tini
CMD ["/app/run.sh"]