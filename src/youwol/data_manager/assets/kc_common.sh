#!/bin/bash

# This will only work with bash, not POSIX sh
exec 2> >(tee "$PATH_WORK_DIR/script_err.log")
exec > >(tee "$PATH_WORK_DIR/script_out.log")

# INT on error, debug everything
set -ex
set -o pipefail

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

die() {
  msg=$1
  echo "Fatal: $msg"
  status "ERROR"
  exit 1
}

kc_adm="/opt/keycloak/bin/kcadm.sh"
kc_adm_configured=0

config_credentials() {
  if [ "x$kc_adm_configured" != "x1" ]; then
    $kc_adm config credentials \
      --server https://$KC_HOSTNAME/auth \
      --realm master \
      --user "$KEYCLOAK_ADMIN" \
      --password "$KEYCLOAK_ADMIN_PASSWORD"
    kc_adm_configured=1
  fi
}

get_realm_id() {
  realm="youwol"
  config_credentials
  rid=$($kc_adm get "realms/$realm" \
          --fields id \
          --format csv \
          --noquotes)
	if [ -z "$rid" ]; then die "realm $realm not found" ; fi
  echo "$rid"
}

get_client_id() {
	client_id="$1"
	config_credentials
	cid=$($kc_adm get clients \
	        --target-realm youwol \
	        --fields id \
	        --query clientId="$client_id" \
	        --format csv \
	        --noquotes)
	if [ -z "$cid" ]; then die "client $client_id not found" ; fi
	echo "$cid"
}

update_client() {
	client_id="$1"
	set_param="$2"
	cid=$(get_client_id "$client_id")
	$kc_adm update "clients/$cid" --target-realm youwol --set "$set_param"
}

set_client_secret() {
	client_id="$1"
	client_secret="$2"
	update_client "$client_id" "secret=$client_secret"
}

set_client_redirect_uris() {
	client_id="$1"
	redirect_uris="$2"
	update_client "$client_id" "redirectUris=[$redirect_uris]"
}

kc_sh="/opt/keycloak/bin/kc.sh"
if [ -z "$KEYCLOAK_IMAGE_OPTIMIZED" ]; then
  status BUILDING
  $kc_sh build | tee "$PATH_WORK_DIR/build.log"
  $kc_sh show-config | tee "$PATH_WORK_DIR/build.config"
  status BUILD
  kc_import="$kc_sh import"
  kc_export="$kc_sh export"
else
  kc_import="$kc_sh import --optimized"
  kc_export="$kc_sh export --optimized"
fi
