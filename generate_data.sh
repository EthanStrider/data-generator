#!/bin/bash

DG_DIRECTORY_PATH="./examples"
DG_ELASTICSEARCH_HOST="my_elasticsearch_instance.us-central1.gcp.cloud.es.io:9243"
DG_ELASTICSEARCH_USER="elastic"
DG_ELASTICSEARCH_PASS="super_secure"
UPLOAD_TO_ELASTICSEARCH=false

python3 ./generate_data_from_yaml.py --folder $DG_DIRECTORY_PATH || exit 1

if [ "$UPLOAD_TO_ELASTICSEARCH" = true ]; then
  python3 ./load_data.py \
          --folder $DG_DIRECTORY_PATH \
          --thread_count 1 \
          --chunk_size 500 \
          --es_host $DG_ELASTICSEARCH_HOST \
          --es_user $DG_ELASTICSEARCH_USER \
          --es_password $DG_ELASTICSEARCH_PASS \
          --format "json" \
          --use_ssl \
          --delete_existing || exit 1
fi