# syntax=docker/dockerfile:1
# check=error=true

FROM chrislusf/seaweedfs

# Install envsubst
ENV BUILD_DEPS="gettext"  \
    RUNTIME_DEPS="libintl"

RUN set -x && \
    apk add --update $RUNTIME_DEPS && \
    apk add --virtual build_deps $BUILD_DEPS &&  \
    cp /usr/bin/envsubst /usr/local/bin/envsubst && \
    apk del build_deps

# Expected environment variables:
# - S3_ACCESS_KEY
# - S3_SECRET_KEY

COPY s3.json.template /s3.json.template
COPY entrypoint.sh /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
