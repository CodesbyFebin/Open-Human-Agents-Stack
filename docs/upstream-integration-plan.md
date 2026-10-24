# Octop, OpenHuman and Andee integration review

This proposal maintains OpenMinds as the primary repository and keeps upstream repositories independently licensed and upgradable. It is **not** a claim of merged functionality or a production integration.

## Matrix

| Project | Useful contribution | Checked upstream license | Integration boundary | Status |
|---|---|---|---|---|
| [Octop](https://github.com/TencentCloud/Octop) | Multi-user experts, IM channels, MCP/OAuth connectors, knowledge, desktop/browser affordances | MIT | Independently deployed service with a scoped gateway identity | Source reviewed; adapter not wired |
| [OpenHuman](https://github.com/tinyhumansai/openhuman) | Rust agent harness, desktop agent operations, tool search | GPL-3.0 | Independently operated agent runtime with an explicit IPC/API contract | Source reviewed; GPL obligations review required |
| [Andee](https://github.com/kuafuai/andee) | Local Android/macOS device agent, device interactions and memory controls | Modified Apache-2.0 with additional terms | Local-only evaluation, no bundled OpenMinds service | Integration blocked pending written permission for third-party multi-tenant/device-product use |

### Important licensing notes

- Octop MIT source can be reused subject to its notice and attribution requirements.
- OpenHuman is GPL-3.0; copying its files into OpenMinds may trigger copyleft distribution obligations. This patch copies **none**.
- Andee is **not standard Apache-2.0**. Its Part A disallows white-labeling; prohibits operating it as a service controlling third-party devices without written approval; and requires written authorization for inclusion as a component of another distributed product. Do not package or expose it as a hosted service without permission from KUAFUAI. Consult qualified legal counsel for distribution decisions.
- No code, icons or trademarks from these projects have been imported. The local checkout script only clones unmodified repositories into an ignored evaluation directory.

## Opt-in clone for local research

```bash
bash scripts/clone-agent-upstreams.sh
git status --short
```

The script refuses unexpected destination paths, does not overwrite existing clones, and logs each HEAD SHA. Review each upstream `LICENSE`, `NOTICE`, and dependency tree before considering modifications. Never commit the `.upstream-sources/` directory or its secrets.

## Functional integration gates

1. **Architecture**: document stable API/IPC, lifecycles, compatibility and data ownership. Octop is Python 3.12+; OpenHuman is Rust; Andee is Kotlin and device-native.
2. **Security**: authenticate both sides of any bridge; map human/agent identity and tenant; enforce capability grants server-side; restrict network and filesystem access.
3. **Execution**: implement separately deployable adapters with opt-in configuration; bounded queues, timeouts, cancellation, idempotency, and evidence receipts. No shared database writes.
4. **Verification**: contract tests with disposable accounts, crash/restart and tenant isolation tests; independently test hostile tools and mobile permissions.
5. **Release**: finish license review (and written Andee permissions if applicable), SBOM, version pinning, provenance notices, CI integration, rollback, and independent security review.

Current registry at `integrations/upstreams.json` is metadata only. It is deliberately fail-closed and is not a runtime dispatcher.
