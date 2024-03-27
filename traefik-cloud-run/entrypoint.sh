#!/bin/sh

SHARED_KEY="${SHARED_KEY:-empty}" \
AGENTS_API_KEY="${AGENTS_API_KEY:-empty}" \
MODEL_API_KEY="${MODEL_API_KEY:-empty}" \
API_KEY="${API_KEY:-empty}" \
MODEL_API_URL="${MODEL_API_URL:-empty}" \
AGENTS_API_URL="${AGENTS_API_URL:-empty}" \
envsubst < /etc/traefik/traefik.yml.template > /etc/traefik/traefik.yml
exec traefik