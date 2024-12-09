# syntax=docker/dockerfile:1
# check=error=true
# We need to build the cozo binary first from the repo
# https://github.com/cozodb/cozo
# Then copy the binary to the ./bin directory
# Then copy the run.sh script to the ./run.sh file

# First stage: Build the Rust project
FROM rust:1.80.1-bookworm AS builder

# Install required dependencies
RUN apt-get update && apt-get install -y \
    liburing-dev \
    libclang-dev \
    clang

# Build cozo-ce-bin from crates.io
WORKDIR /usr/src
RUN cargo install cozo-ce-bin@0.7.13-alpha.1 --features "requests graph-algo storage-new-rocksdb storage-sqlite jemalloc io-uring malloc-usable-size"

# Copy the built binary to /usr/local/bin
RUN cp /usr/local/cargo/bin/cozo-ce-bin /usr/local/bin/cozo

# -------------------------------------------------------------------------------------------------

# Second stage: Create the final image
FROM debian:bookworm-slim

# Install dependencies
RUN \
    apt-get update -yqq && \
    apt-get install -y \
        ca-certificates tini nfs-common nfs-kernel-server procps netbase \
        liburing-dev curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Set fallback mount directory
ENV COZO_MNT_DIR=/data COZO_BACKUP_DIR=/backup APP_HOME=/app COZO_PORT=9070
WORKDIR $APP_HOME

# Copy the cozo binary
COPY --from=builder /usr/local/bin/cozo $APP_HOME/bin/cozo

# Copy local code to the container image.
COPY ./run.sh ./run.sh
COPY ./backup.sh ./backup.sh

# Ensure the script is executable
RUN \
    mkdir -p $COZO_MNT_DIR $COZO_BACKUP_DIR && \
    chmod +x $APP_HOME/bin/cozo && \
    chmod +x $APP_HOME/run.sh

# Copy the options file into the image
COPY ./options ./options

# Use tini to manage zombie processes and signal forwarding
# https://github.com/krallin/tini
ENTRYPOINT ["/usr/bin/tini", "--"]

# Pass the startup script as arguments to tini
CMD ["/app/run.sh"]
