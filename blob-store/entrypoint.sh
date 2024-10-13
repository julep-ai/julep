#!/bin/sh

set -e

# Check the environment variables
for var_name in S3_ACCESS_KEY S3_SECRET_KEY
do
    if [ -z "`eval echo \\\$$var_name`" ]; then
        echo "Error: Environment variable '$var_name' is not set."
        exit 1
    fi
done

# Generate the s3.json configuration file
envsubst < /s3.json.template > /s3.json

if [ "$DEBUG" = "true" ]; then
    echo '@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@'
    echo '@@@ Careful: Debug mode is enabled. @@@'
    echo '@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@'

    echo 'Printing s3.json:'
    cat /s3.json
fi

# Forward all arguments to the seaweedfs binary
exec weed server -s3.config=/s3.json "$@"
