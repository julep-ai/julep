# syntax=docker/dockerfile:1
# check=error=true

FROM alpine/git
ARG PLUGIN_MODULE=github.com/julep-ai/traefik-jwt-plugin
ARG PLUGIN_GIT_REPO=https://github.com/julep-ai/traefik-jwt-plugin.git
ARG PLUGIN_GIT_BRANCH=main
RUN git clone ${PLUGIN_GIT_REPO} /plugins-local/src/${PLUGIN_MODULE} \
      --depth 1 --single-branch --branch ${PLUGIN_GIT_BRANCH}

#################

# TODO: Upgrade to Traefik v3
FROM traefik:v2.11

ENV GATEWAY_PORT=80
ENV AGENTS_API_URL=""

# Expected environment variables:
# JWT_SHARED_KEY=""
# AGENTS_API_KEY=""
# AGENTS_API_KEY_HEADER_NAME="Authorization"

COPY --from=0 /plugins-local /plugins-local

RUN apk add gettext
RUN mkdir -p /etc/traefik
COPY traefik.yml.template /etc/traefik/
COPY entrypoint.sh /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
