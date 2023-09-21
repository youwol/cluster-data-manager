#!/bin/bash

source ${PATH_KEYCLOAK_COMMON_SCRIPT}

status IMPORTING
$kc_import \
  --override true \
  --dir "$PATH_WORK_DIR" \
  | tee "$PATH_WORK_DIR/import.log"
status IMPORTED

status DONE
