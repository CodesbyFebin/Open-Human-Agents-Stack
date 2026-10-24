#!/usr/bin/env bash
set -euo pipefail

CERT_DIR="/etc/openminds/certs"
mkdir -p "${CERT_DIR}"
chmod 700 "${CERT_DIR}"

log_info() {
    echo -e "\033[1;34m[PKI_BOOTSTRAP] $(date -u +'%Y-%m-%dT%H:%M:%SZ') - INFO -\033[0m $1"
}

log_error() {
    echo -e "\033[1;31m[PKI_BOOTSTRAP] $(date -u +'%Y-%m-%dT%H:%M:%SZ') - ERROR -\033[0m $1" >&2
}

if [[ -f "${CERT_DIR}/ca.crt" && -f "${CERT_DIR}/server.crt" ]]; then
    log_info "Immutable authority anchor matrices already mounted. Skipping generation loops."
    exit 0
fi

log_info "Commencing dynamic cryptographic certificate compilation loop..."

cat <<EOF > "${CERT_DIR}/ca.conf"
[req]
distinguished_name = req_distinguished_name
prompt = no
[req_distinguished_name]
O = OpenMinds Autonomous Fleet System
CN = OpenMinds Root CA v2
C = IN
ST = Kerala
L = Ernakulam
EOF

openssl genrsa -out "${CERT_DIR}/ca.key" 4096
openssl req -new -x509 -days 3650 -key "${CERT_DIR}/ca.key" -out "${CERT_DIR}/ca.crt" -config "${CERT_DIR}/ca.conf"

cat <<EOF > "${CERT_DIR}/server.conf"
[req]
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no
[req_distinguished_name]
O = OpenMinds Compute Central Control Plane
CN = om-core-backend
[v3_req]
keyUsage = keyEncipherment, dataEncipherment
extendedKeyUsage = serverAuth, clientAuth
subjectAltName = @alt_names
[alt_names]
DNS.1 = om-core-backend
DNS.2 = localhost
IP.1 = 127.0.0.1
EOF

openssl genrsa -out "${CERT_DIR}/server.key" 2048
openssl req -new -key "${CERT_DIR}/server.key" -out "${CERT_DIR}/server.csr" -config "${CERT_DIR}/server.conf"
openssl x509 -req -days 730 -in "${CERT_DIR}/server.csr" -CA "${CERT_DIR}/ca.crt" -CAkey "${CERT_DIR}/ca.key" -CAcreateserial -out "${CERT_DIR}/server.crt" -extfile "${CERT_DIR}/server.conf" -extensions v3_req

rm -f "${CERT_DIR}/ca.conf" "${CERT_DIR}/server.conf" "${CERT_DIR}/server.csr" "${CERT_DIR}/ca.srl"
chmod 600 "${CERT_DIR}/ca.key" "${CERT_DIR}/server.key"
chmod 644 "${CERT_DIR}/ca.crt" "${CERT_DIR}/server.crt"

log_info "Cryptographic handshake keys successfully mounted. Operational boundaries locked."
