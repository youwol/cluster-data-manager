#!/bin/bash

# This will only work with bash, not POSIX sh
exec 2> >(tee "$PATH_WORK_DIR/script_err.log")
exec > >(tee "$PATH_WORK_DIR/script_out.log")

# INT on error, debug everything
set -ex

trap "echo 'Trapping SIGINT. The script ended with errors'; echo 'ERROR' > '$PATH_KEYCLOAK_STATUS_FILE'; exit 1" INT
trap "echo 'Trapping SIGTERM . The script ended with errors'; echo 'ERROR' > '$PATH_KEYCLOAK_STATUS_FILE'; exit 1" TERM
trap "echo 'Trapping SIGABRT. The script ended with errors'; echo 'ERROR' > '$PATH_KEYCLOAK_STATUS_FILE'; exit 1" ABRT
trap "echo 'Trapping SIGQUIT. The script ended with errors'; echo 'ERROR' > '$PATH_KEYCLOAK_STATUS_FILE'; exit 1" QUIT
trap "echo 'Trapping error. The script ended with errors'; echo 'ERROR' > '$PATH_KEYCLOAK_STATUS_FILE'; exit 1" ERR

status_file="$PATH_KEYCLOAK_STATUS_FILE"
status() {
  status="$1"
  echo "$status" > "$status_file"
  echo
  echo "STATUS=$status"
}
status INIT

status BUILDING
/opt/keycloak/bin/kc.sh build | tee "$PATH_WORK_DIR/build.log"
status BUILD

status EXPORTING
/opt/keycloak/bin/kc.sh export \
  --realm youwol \
  --users different_files --users-per-file 100 \
  --dir "$PATH_WORK_DIR" \
  | tee "$PATH_WORK_DIR/export.log"
status EXPORTED

status DONE
