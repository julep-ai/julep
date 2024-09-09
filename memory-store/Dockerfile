# We need to build the cozo binary first from the repo
# https://github.com/cozodb/cozo
# Then copy the binary to the ./bin directory
# Then copy the run.sh script to the ./run.sh file

# First stage: Build the Rust project
FROM rust:1.80.1-bookworm AS builder

# Install liburing-dev
RUN apt-get update && apt-get install -y liburing-dev

# Clone the CozoDB repository with submodules (checkout the specified commit)
ARG COZO_COMMIT=57b7b440fd93440d985f2259eeaaf2ba5cc7569e
RUN \
    git clone --depth 1 --recurse-submodules --shallow-submodules https://github.com/cozodb/cozo.git /usr/src/cozo && \
    cd /usr/src/cozo && \
    git checkout $COZO_COMMIT

# Set the working directory
WORKDIR /usr/src/cozo
# Build CozoDB
RUN cargo build --release -p cozo-bin --features "requests graph-algo storage-rocksdb storage-sqlite jemalloc io-uring"

# Copy the built binary to /usr/local/bin
RUN cp target/release/cozo-bin /usr/local/bin/cozo

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

# Use tini to manage zombie processes and signal forwarding
# https://github.com/krallin/tini
ENTRYPOINT ["/usr/bin/tini", "--"]

# Pass the startup script as arguments to tini
CMD ["/app/run.sh"]