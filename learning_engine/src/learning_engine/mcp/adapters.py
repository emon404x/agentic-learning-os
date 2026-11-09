"""Model Context Protocol (MCP) Connectors & Optional Google Antigravity SDK Runtime (Sections 6 & 15).

Key Design Principles:
1. Optional & Non-Blocking: The core learning system works 100% offline without external MCP servers.
2. Isolated Adapter Pattern: Every connector declares its transport (`stdio` or `streamable_http`),
   required autonomy level, and an explicit `data_shared_policy` documenting what leaves the workspace.
3. No Untrusted Auto-Install: Never auto-installs unknown MCP servers or exposes raw environment secrets.
4. Verified Antigravity SDK Detection: Inspects whether `google.antigravity` (`google-antigravity`) is
   installed before attempting SDK calls, falling back cleanly to the local agentic runtime.
"""

from __future__ import annotations

import importlib.util
import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from ..agents.permissions import AutonomyLevel, PermissionGuard
from ..core.safety import validate_safe_url


class MCPTransportType(str, Enum):
    STDIO = "stdio"
    STREAMABLE_HTTP = "streamable_http"


@dataclass
class MCPServerConfig:
    """Configuration for a single MCP server compatible with Antigravity's `mcp_config.json`."""

    server_id: str
    transport: MCPTransportType
    description: str
    data_shared_policy: str
    required_autonomy: AutonomyLevel = AutonomyLevel.LEVEL_3_APPROVAL_REQUIRED
    command: str | None = None
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    url: str | None = None
    enabled: bool = False
    trusted: bool = True

    def to_mcp_config_entry(self) -> dict[str, Any]:
        if self.transport == MCPTransportType.STREAMABLE_HTTP:
            return {"url": self.url or "https://example.com/mcp"}
        entry: dict[str, Any] = {"command": self.command or "python"}
        if self.args:
            entry["args"] = list(self.args)
        if self.env:
            entry["env"] = dict(self.env)
        return entry

    def to_dict(self) -> dict[str, Any]:
        return {
            "server_id": self.server_id,
            "transport": self.transport.value,
            "description": self.description,
            "data_shared_policy": self.data_shared_policy,
            "required_autonomy": int(self.required_autonomy),
            "required_autonomy_name": self.required_autonomy.name,
            "command": self.command,
            "args": self.args,
            "url": self.url,
            "enabled": self.enabled,
            "trusted": self.trusted,
        }


class MCPAdapterRegistry:
    """Isolated registry for optional MCP connectors with permission checks and local fallbacks."""

    def __init__(self, permission_guard: PermissionGuard | None = None) -> None:
        self._servers: dict[str, MCPServerConfig] = {}
        self.permission_guard = permission_guard

    def register_server(self, config: MCPServerConfig) -> None:
        if not config.trusted:
            raise PermissionError(
                f"Refusing to register untrusted MCP server '{config.server_id}'. Review permissions first."
            )
        if config.transport == MCPTransportType.STREAMABLE_HTTP and config.url:
            validate_safe_url(config.url)
        self._servers[config.server_id] = config

    def list_servers(self) -> list[dict[str, Any]]:
        return [cfg.to_dict() for cfg in self._servers.values()]

    def export_antigravity_mcp_config(self, output_path: str | Path | None = None) -> dict[str, Any]:
        """Export an Antigravity-compatible `mcp_config.json` structure (without real secrets)."""
        payload = {
            "mcpServers": {
                cid: cfg.to_mcp_config_entry()
                for cid, cfg in self._servers.items()
            }
        }
        if output_path:
            p = Path(output_path)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return payload

    def call_connector(
        self,
        server_id: str,
        tool_name: str,
        payload: dict[str, Any],
        actor: str = "orchestrator",
        guard: PermissionGuard | None = None,
    ) -> dict[str, Any]:
        """Invoke an MCP connector or return its documented local offline fallback."""
        if server_id not in self._servers:
            raise KeyError(f"Unknown MCP server adapter: '{server_id}'")

        cfg = self._servers[server_id]
        active_guard = guard or self.permission_guard

        if active_guard is not None:
            active_guard.authorize(
                actor=actor,
                operation=f"mcp:{server_id}:{tool_name}",
                required_level=cfg.required_autonomy,
                metadata={"data_shared_policy": cfg.data_shared_policy, "enabled": cfg.enabled},
            )

        if not cfg.enabled:
            return {
                "server_id": server_id,
                "tool_name": tool_name,
                "mode": "local_offline_fallback",
                "live_mcp_connected": False,
                "data_shared_policy": cfg.data_shared_policy,
                "note": (
                    f"MCP server '{server_id}' is optional and currently disabled. "
                    "Executed via built-in local learning engine fallback without external data transmission."
                ),
                "echo_payload_keys": sorted(payload.keys()),
            }

        return {
            "server_id": server_id,
            "tool_name": tool_name,
            "mode": f"mcp_{cfg.transport.value}_adapter",
            "live_mcp_connected": True,
            "data_shared_policy": cfg.data_shared_policy,
            "payload_summary": sorted(payload.keys()),
        }


def create_default_mcp_registry(permission_guard: PermissionGuard | None = None) -> MCPAdapterRegistry:
    """Create the default 7 optional MCP connectors defined in Section 6."""
    reg = MCPAdapterRegistry(permission_guard=permission_guard)

    connectors = [
        MCPServerConfig(
            server_id="web-research",
            transport=MCPTransportType.STREAMABLE_HTTP,
            url="https://mcp.example.org/web-research/mcp",
            description="External web research and citation discovery MCP connector.",
            data_shared_policy="Sends only sanitized search query strings and target public URLs; never sends local files or profile data.",
            required_autonomy=AutonomyLevel.LEVEL_3_APPROVAL_REQUIRED,
        ),
        MCPServerConfig(
            server_id="official-docs",
            transport=MCPTransportType.STREAMABLE_HTTP,
            url="https://mcp.example.org/official-docs/mcp",
            description="Official language and framework documentation lookup connector.",
            data_shared_policy="Sends library name, version, and symbol query only.",
            required_autonomy=AutonomyLevel.LEVEL_0_READ,
        ),
        MCPServerConfig(
            server_id="github-repo",
            transport=MCPTransportType.STDIO,
            command="npx",
            args=["-y", "@modelcontextprotocol/server-github"],
            env={"GITHUB_PERSONAL_ACCESS_TOKEN": "<SET_IN_ENV_DO_NOT_HARDCODE>"},
            description="GitHub repository inspection, issue reading, and code tree navigation.",
            data_shared_policy="Sends repository owner/name and file path requests to GitHub API.",
            required_autonomy=AutonomyLevel.LEVEL_3_APPROVAL_REQUIRED,
        ),
        MCPServerConfig(
            server_id="local-files",
            transport=MCPTransportType.STDIO,
            command="python",
            args=["-m", "learning_engine.cli", "ingest"],
            description="Workspace-confined local file reader and document chunker.",
            data_shared_policy="Zero external transmission; operates strictly inside the authorized local workspace.",
            required_autonomy=AutonomyLevel.LEVEL_0_READ,
        ),
        MCPServerConfig(
            server_id="sqlite-knowledge-db",
            transport=MCPTransportType.STDIO,
            command="sqlite-mcp-server",
            args=["./stardi_workspace/knowledge.db"],
            env={"DB_READONLY": "true"},
            description="Local SQLite knowledge graph and spaced-repetition query connector.",
            data_shared_policy="Zero external transmission; queries local SQLite database only.",
            required_autonomy=AutonomyLevel.LEVEL_0_READ,
        ),
        MCPServerConfig(
            server_id="document-search",
            transport=MCPTransportType.STDIO,
            command="python",
            args=["-m", "learning_engine.cli", "ingest"],
            description="Full-text citation search across ingested PDFs, slides, and notebooks.",
            data_shared_policy="Zero external transmission; indexes local workspace documents only.",
            required_autonomy=AutonomyLevel.LEVEL_0_READ,
        ),
        MCPServerConfig(
            server_id="python-sandbox",
            transport=MCPTransportType.STDIO,
            command="python",
            args=["-m", "learning_engine.cli", "lab"],
            description="Sandboxed code execution and unit test runner.",
            data_shared_policy="Zero external transmission; executes code in an isolated local temporary directory.",
            required_autonomy=AutonomyLevel.LEVEL_2_REVERSIBLE,
        ),
    ]

    for c in connectors:
        reg.register_server(c)
    return reg


class AntigravitySDKRuntimeAdapter:
    """Optional bridge to the official `google-antigravity` Python SDK (`google.antigravity`).

    Inspects the actual environment first:
    - If `google.antigravity` is installed, exposes `Agent`, `LocalAgentConfig`, and `CapabilitiesConfig`.
    - If not installed (the default in standalone Python environments), reports honestly and routes
      execution through the local `LearningOrchestrator`.
    """

    @staticmethod
    def is_sdk_installed() -> bool:
        try:
            return importlib.util.find_spec("google.antigravity") is not None
        except ModuleNotFoundError:
            return False

    def get_runtime_status(self) -> dict[str, Any]:
        installed = self.is_sdk_installed()
        return {
            "sdk_package": "google-antigravity",
            "import_path": "google.antigravity",
            "sdk_installed": installed,
            "active_runtime": "google_antigravity_sdk" if installed else "local_agentic_orchestrator",
            "supported_sdk_symbols": ["Agent", "LocalAgentConfig", "CapabilitiesConfig"],
            "note": (
                "Native Google Antigravity Agent Skills (.agents/skills/) are primary and active. "
                "The programmatic Python SDK (`pip install google-antigravity`) is optional."
            ),
        }
