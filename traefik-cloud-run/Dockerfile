FROM alpine:3
ARG PLUGIN_MODULE=github.com/julep-ai/traefik-jwt-plugin
ARG PLUGIN_GIT_REPO=https://github.com/julep-ai/traefik-jwt-plugin.git
ARG PLUGIN_GIT_BRANCH=main
RUN apk add --update git && \
    git clone ${PLUGIN_GIT_REPO} /plugins-local/src/${PLUGIN_MODULE} \
      --depth 1 --single-branch --branch ${PLUGIN_GIT_BRANCH}

#################

FROM traefik:v2.11

COPY --from=0 /plugins-local /plugins-local

RUN apk add gettext
RUN mkdir -p /etc/traefik
COPY traefik.yml.template /etc/traefik/
COPY entrypoint.sh /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
