#!/usr/bin/env sh

gcloud run deploy julep-cozo-server-1 --source . \
    --vpc-connector vpc-connector-1 \
    --execution-environment gen2 \
    --allow-unauthenticated \
    --service-account cozo-nfs-identity \
    --update-env-vars FILESTORE_IP_ADDRESS=`gcloud filestore instances describe julep-nfs-1 --format "value(networks.ipAddresses[0])"`,FILE_SHARE_NAME=cozo_data,COZO_ROCKSDB_FILE=september_19_2023.cozo.db
