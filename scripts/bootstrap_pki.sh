#!/usr/bin/env bash
# Developer/staging PKI bootstrap. Production CAs require managed lifecycle and revocation.
set -euo pipefail
: "${OM_CERT_DIR:?Set OM_CERT_DIR to a dedicated private certificate directory}"
: "${OM_RUNNER_ID:=dev-runner}"
if [[ ! "$OM_RUNNER_ID" =~ ^[a-zA-Z0-9_-]{1,64}$ ]]; then
  echo "Invalid runner ID" >&2
  exit 2
fi
case "$OM_CERT_DIR" in
  /*) ;;
  *) echo "OM_CERT_DIR must be an absolute path" >&2; exit 2 ;;
esac
if [[ "$OM_CERT_DIR" == "/" || "$OM_CERT_DIR" == "/etc" || "$OM_CERT_DIR" == "/tmp" ]]; then
  echo "OM_CERT_DIR must name a dedicated directory" >&2
  exit 2
fi
umask 077
mkdir -p "$OM_CERT_DIR" "$OM_CERT_DIR/runners/$OM_RUNNER_ID"
chmod 700 "$OM_CERT_DIR" "$OM_CERT_DIR/runners" "$OM_CERT_DIR/runners/$OM_RUNNER_ID"
ca="$OM_CERT_DIR/ca.crt"
ca_key="$OM_CERT_DIR/ca.key"
server="$OM_CERT_DIR/server.crt"
server_key="$OM_CERT_DIR/server.key"
runner_dir="$OM_CERT_DIR/runners/$OM_RUNNER_ID"
if [[ -e "$ca" || -e "$ca_key" || -e "$server" || -e "$server_key" ]]; then
  echo "Existing PKI material detected; refusing to overwrite. Use a new dedicated directory for rotation." >&2
  exit 2
fi
openssl req -x509 -newkey rsa:3072 -sha256 -nodes -days 365 -subj "/CN=OpenMinds Development CA" \
  -addext "basicConstraints=critical,CA:TRUE" \
  -addext "keyUsage=critical,keyCertSign,cRLSign" \
  -keyout "$ca_key" -out "$ca"
openssl req -new -newkey rsa:2048 -sha256 -nodes -subj "/CN=openminds-control-plane" \
  -keyout "$server_key" -out "$OM_CERT_DIR/server.csr"
openssl x509 -req -sha256 -days 90 -in "$OM_CERT_DIR/server.csr" \
  -CA "$ca" -CAkey "$ca_key" -CAcreateserial -out "$server" \
  -extfile <(printf '%s\n' 'basicConstraints=CA:FALSE' 'extendedKeyUsage=serverAuth' 'keyUsage=digitalSignature,keyEncipherment' 'subjectAltName=DNS:control-plane,DNS:localhost,IP:127.0.0.1')
openssl req -new -newkey rsa:2048 -sha256 -nodes -subj "/CN=runner-$OM_RUNNER_ID" \
  -keyout "$runner_dir/runner.key" -out "$runner_dir/runner.csr"
openssl x509 -req -sha256 -days 90 -in "$runner_dir/runner.csr" \
  -CA "$ca" -CAkey "$ca_key" -CAserial "$OM_CERT_DIR/ca.srl" \
  -out "$runner_dir/runner.crt" \
  -extfile <(printf '%s\n' 'basicConstraints=CA:FALSE' 'extendedKeyUsage=clientAuth' 'keyUsage=digitalSignature')
openssl verify -CAfile "$ca" -purpose sslserver "$server"
openssl verify -CAfile "$ca" -purpose sslclient "$runner_dir/runner.crt"
rm -f "$OM_CERT_DIR/server.csr" "$runner_dir/runner.csr" "$OM_CERT_DIR/ca.srl"
chmod 600 "$ca_key" "$server_key" "$runner_dir/runner.key"
chmod 644 "$ca" "$server" "$runner_dir/runner.crt"
echo "PKI files created. Mount only ca.crt plus the relevant endpoint certificate/key; never mount ca.key in a runner."
