#!/bin/bash

source ${PATH_KEYCLOAK_COMMON_SCRIPT}

status IMPORTING
$kc_import \
  --override true \
  --dir "$PATH_WORK_DIR" \
  | tee "$PATH_WORK_DIR/import.log"
status IMPORTED

if [ -n "$KEYS_ROTATION" ]; then
  status ROTATING_KEYS
  if [ "x$KEYS_ROTATION" == "xrotate" ]; then
    deactivate_existing_keys
  elif [ "x$KEYS_ROTATION" == "xreset" ]; then
    delete_existing_keys
  else
    die "Env KEYS_ROTATION has invalid value '$KEYS_ROTATION'"
  fi
  insert_new_keys
fi

status CONFIGURING_CLIENTS
set_client_secret admin-cli "$ADMIN_CLI_CLIENT_SECRET"
set_client_secret integration-tests "$INTEGRATION_TESTS_CLIENT_SECRET"
set_client_secret youwol-platform "$YOUWOL_PLATFORM_CLIENT_SECRET"
set_client_redirect_uris youwol-platform "$YOUWOL_PLATFORM_CLIENT_REDIRECT_URIS"
set_client_secret webpm "$WEBPM_CLIENT_SECRET"

status DONE
