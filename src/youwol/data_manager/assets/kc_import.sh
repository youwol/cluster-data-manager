#!/bin/bash

source ${PATH_KEYCLOAK_COMMON_SCRIPT}

status IMPORTING
$kc_import \
  --override true \
  --dir "$PATH_WORK_DIR" \
  | tee "$PATH_WORK_DIR/import.log"
status IMPORTED

status CONFIGURING_CLIENTS
set_client_secret admin-cli "$ADMIN_CLI_CLIENT_SECRET"
set_client_secret integration-tests "$INTEGRATION_TESTS_CLIENT_SECRET"
set_client_secret youwol-platform "$YOUWOL_PLATFORM_CLIENT_SECRET"
set_client_redirect_uris youwol-platform "$YOUWOL_PLATFORM_CLIENT_REDIRECT_URIS"
set_client_secret webpm "$WEBPM_CLIENT_SECRET"

status DONE
