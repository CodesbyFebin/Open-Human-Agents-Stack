# Runner PKI and mTLS qualification

This phase establishes isolated development certificate issuance and an explicit health diagnostic. It does **not** implement mutual-TLS transport enforcement between Go runners and FastAPI, and issue #2 must stay open.

## Generate dedicated material (development/staging only)

```bash
export OM_CERT_DIR=/absolute/private/path/openminds-certs
export OM_RUNNER_ID=runner-one
bash scripts/bootstrap_pki.sh
```

The script creates a CA, a server certificate, and a runner client certificate. It verifies both chains, applies restrictive private-key modes and refuses to overwrite an existing CA. Never commit the output.

### Mounting boundaries

- API service receives: `ca.crt`, `server.crt`, `server.key` (read-only).
- Runner `runner-one` receives: `ca.crt`, `runners/runner-one/runner.crt` and its own `runner.key` only.
- **Never** mount `ca.key` into API or runners. Keep it offline in a protected enrollment environment.
- No runner client certificate is injected into the generic Compose service automatically; enrollment and fleet identity authorization need a concrete runner runtime.

`/health.cryptoStatus.material_loadable` reports whether the API can load the configured certificate/key material. `mutual_tls_enforced` deliberately remains **false** until both parties authenticate a real TLS connection and certificate identity is bound to the runner registration.

## Required final tests

1. True mTLS handshake rejects missing, expired, forged, revoked and wrong-runner certificates.
2. Certificate rotation and service restart do not disclose private keys.
3. Runner registration and heartbeat identities are derived from TLS peer identity, not self-reported request fields.
4. Staging fleet mounts correct per-runner secrets and tests recovery after cert expiry.
5. Independent security review, short-lived issuance, audit trails and a revocation story.

The current Go `backend/pkg/security/pki.go` is source for future signing integration, but no claim is made that its issuance functions are wired into a live enrollment endpoint.
