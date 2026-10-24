# Bounded Compose deployment candidate

The canonical configuration for **integration qualification** is `docker/compose.production.yml`.
The existing `docker/docker-compose.yml`, `docker/docker-compose.prod.yml` and `docker/docker-compose.extensions.yml` are historical prototypes. Do not merge them with `-f`: they use incompatible service names, unverified images, and conflicting networking assumptions. This is not a production release endorsement.

## Safe local qualification

Set `OM_DB_PASSWORD` to a strong URL-safe random value, `OM_CERT_DIR` to an absolute directory containing the certificate files emitted by the PKI bootstrap process, and public URLs to the reachable API origin.

```bash
export OM_DB_PASSWORD='REPLACE_WITH_LONG_URL_SAFE_RANDOM_PASSWORD'
export OM_CERT_DIR='/absolute/path/to/private/openminds/certs'
docker compose -f docker/compose.production.yml config --quiet
docker compose -f docker/compose.production.yml up -d --build --wait
curl --fail http://127.0.0.1:8000/health
docker compose -f docker/compose.production.yml ps
```

Stop without deleting persistent data:

```bash
docker compose -f docker/compose.production.yml down
```

### Boundaries enforced by the candidate

- Database and Redis have no host-published ports, on an internal bridge network.
- Web and API ports bind only to loopback. Put a separately configured TLS reverse proxy and authenticated access layer in front before remote access.
- The control plane has **no Docker socket** and drops Linux capabilities; this also means Docker-based worker dispatch is **not** enabled through this deployment.
- Certificate folder is mounted read-only but application mTLS enforcement is **not yet implemented**.
- No privileged, unverified image or GPU device is mounted. Appwrite, ComfyUI and mobile bridge require separately reviewed optional service manifests; they are **not enabled**.
- Database data remains in a named volume. The schema init runs on a *new* volume only; existing volumes need tested migrations and backups.
- Container health checks prove liveness only, not tenant isolation, authorization or recovery.

### Required release gates not satisfied by boot

1. Pin and lock image/dependency digests; include a committed Node lockfile and SBOM.
2. Enforce authentication, tenant isolation, CSRF/CORS limits, rate limits, secrets rotation and security audit.
3. Prove mTLS enrollment, revocation, expiry and mutual verification for each runner.
4. Prove database migration/backup/restore, resilience, bounded execution and shutdown.
5. Independently review reverse proxy, TLS, observability, logs and rollback.
6. Explicitly scope Appwrite (needs upstream-supported deployment), GPU hardware, and mobile device permissions.

CI workflow `.github/workflows/compose-hardened.yml` performs ephemeral boot/health proof using disposable credentials and data volumes. It does not exercise external infrastructure.
