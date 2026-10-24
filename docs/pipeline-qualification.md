# Pipeline integration status

Issue #3 requests an end-to-end research → durable coding → Comfy render → human review → vault DAG with PostgreSQL checkpointing.

The API now constructs that five-node DAG. Its executor rejects simulated research and coding output and never treats a timeout or caller-provided approval as a human decision. ComfyUI can submit a real job when `COMFYUI_HOST` is explicitly set, but queue acceptance is **not render completion**.

The default run intentionally returns `blocked` at research, without writing a fabricated success checkpoint. This is a safety remediation, **not** an implemented end-to-end executor.

## Still required

- Authenticated RAG/research connector with verified citations.
- A real isolated coding worker, bounded filesystem and runtime permissions, result hashes and cancellation.
- ComfyUI history/polling, job result verification and artifact acquisition.
- Durable user-bound human review with exact-action authorization and resume tokens; no automatic approval.
- Artifact vault commit with provenance and retention.
- Restart/resume integration tests against disposable PostgreSQL, Redis, worker and render endpoints.
- Independent security review before untrusted prompts may dispatch code or device actions.
