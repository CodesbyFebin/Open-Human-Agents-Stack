# Third-Party Attribution

OpenMinds is original integration work. The following projects provided architectural inspiration. No substantial source code was copied.

| Project | What was inspired | License |
|---------|-------------------|---------|
| Dify | Visual workflow ideas | Apache-2.0 / custom |
| AgentsMesh | Multi-machine runner concepts | check upstream |
| Multica | Team board / handoff concepts | check upstream |
| Pydantic AI | Typed agent patterns | MIT |
| ComfyUI | Node graph rendering concepts | GPL-3.0 |
| Appwrite | BaaS session/artifact ideas | BSD-3 |
| Bytebase | Declarative migration ideas | Apache-2.0 |

If any file is later found to contain copied code, it will be replaced or properly licensed and noted here.

## Newly reviewed upstreams (source reference only)

| Upstream | License | Boundary | Source copied? |
|---|---|---|---|
| TencentCloud/Octop | MIT | Standalone service candidate | No |
| tinyhumansai/openhuman | GPL-3.0 | Separate Rust process evaluation | No |
| kuafuai/andee | Modified Apache-2.0 with additional restrictions | Local device evaluation only; bundling/third-party hosting permission required | No |

See [integration plan](docs/upstream-integration-plan.md). Upstream projects keep their own attribution and branding. No integration is enabled or distributed by default.
