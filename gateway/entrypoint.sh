#!/bin/sh

# Check the environment variables
# REMOVED: MODEL_API_KEY MODEL_API_URL MODEL_API_KEY_HEADER_NAME
for var_name in GATEWAY_PORT JWT_SHARED_KEY AGENTS_API_KEY AGENTS_API_URL AGENTS_API_KEY_HEADER_NAME
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
