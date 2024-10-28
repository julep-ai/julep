#!/bin/sh

# Check the environment variables
AGENTS_API_URL=${AGENTS_API_URL:-http://agents-api:8080}
AGENTS_API_KEY_HEADER_NAME=${AGENTS_API_KEY_HEADER_NAME:-Authorization}
GATEWAY_PORT=${GATEWAY_PORT:-80}
TEMPORAL_UI_PUBLIC_URL=${TEMPORAL_UI_PUBLIC_URL:-http://temporal-ui-public:8080}

for var_name in JWT_SHARED_KEY AGENTS_API_KEY
do
    if [ -z "`eval echo \\\$$var_name`" ]; then
        echo "Error: Environment variable '$var_name' is not set."
        exit 1
    fi
done

# Generate the Traefik configuration file
envsubst < /etc/traefik/traefik.yml.template > /etc/traefik/traefik.yml

# Forward all arguments to the traefik binary
exec traefik "$@"
