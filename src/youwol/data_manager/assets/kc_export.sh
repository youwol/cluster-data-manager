#!/bin/bash

source ${PATH_KEYCLOAK_COMMON_SCRIPT}

status CLEANING
rm "$PATH_WORK_DIR"/youwol-realm.json
rm "$PATH_WORK_DIR"/youwol-users-*.json

status EXPORTING
$kc_export \
  --realm youwol \
  --users different_files --users-per-file 100 \
  --dir "$PATH_WORK_DIR" \
  | tee "$PATH_WORK_DIR/export.log"
status EXPORTED

status DONE
