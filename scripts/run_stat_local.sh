#!/usr/bin/env bash

set -a  # Automatically export all variables
source .env
set +a  # Stop automatically exporting variables

##### VARIABLES
DATA_ROOT_DIR=/Users/hewapathirana/Desktop/transfer_logs_privacy_ready_3 #$LOGS_DESTINATION_ROOT #"/path/to/data/transfer_logs_privacy_ready"
API_BASE_URL=""
API_ENDPOINT_FILE_DOWNLOADS_PER_PROJECT=""
API_ENDPOINT_FILE_DOWNLOADS_PER_FILE=""
API_ENDPOINT_HEADER=""


RESOURCE=$1
echo "RESOURCE : ${RESOURCE}"
PROFILE=$2
echo "PROFILE : ${PROFILE}"

RUN_NAME="nf-downloadstat-$(echo "$RESOURCE" | tr '[:upper:]' '[:lower:]')-$(date +"%Y")-$(date +"%b" | tr '[:upper:]' '[:lower:]')-$((RANDOM % 9000 + 1000))"
LOG_FILE="${LOG_FOLDER}${RUN_NAME}_nextflow.log"

conda activate file_download_stat
nextflow -log $LOG_FILE run ${PIPELINE_BASE_DIR}main.nf \
              -params-file params/$RESOURCE-$PROFILE-params.yml \
              -name $RUN_NAME \
              -profile $PROFILE \
              --root_dir $DATA_ROOT_DIR \
              --log_file $LOG_FILE \
              --api_endpoint_file_downloads_per_project $API_ENDPOINT_FILE_DOWNLOADS_PER_PROJECT \
              --api_endpoint_file_downloads_per_file $API_ENDPOINT_FILE_DOWNLOADS_PER_FILE \
              --api_endpoint_header $API_ENDPOINT_HEADER -resume
#              -with-dag workflow_dag.png \
