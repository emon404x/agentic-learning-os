"""Agentic Safety, Autonomy Control, Loop Prevention, and Execution Auditing (Section 14).

Autonomy Levels:
- LEVEL_0_READ (0): Read materials, research, and analyze.
- LEVEL_1_PLAN (1): Create plans, courses, and recommendations.
- LEVEL_2_REVERSIBLE (2): Create notes, generate files in workspace, and update local learning progress.
- LEVEL_3_APPROVAL_REQUIRED (3): Install packages, modify important existing files, change configurations,
  connect external accounts, make external API calls with costs, or perform consequential actions.
- LEVEL_4_EXPLICIT_CONFIRMATION (4): Delete data, overwrite backups, publish repositories, push Git commits,
  deploy infrastructure, change permissions, or perform irreversible external actions.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import IntEnum
from pathlib import Path
from typing import Any

from ..core.safety import resolve_safe_workspace_path, sanitize_untrusted_text, validate_safe_url


class AutonomyLevel(IntEnum):
    LEVEL_0_READ = 0
    LEVEL_1_PLAN = 1
    LEVEL_2_REVERSIBLE = 2
    LEVEL_3_APPROVAL_REQUIRED = 3
    LEVEL_4_EXPLICIT_CONFIRMATION = 4


AUTONOMY_DESCRIPTIONS: dict[int, str] = {
    AutonomyLevel.LEVEL_0_READ: "LEVEL 0 (READ): Read materials, research, and analyze.",
    AutonomyLevel.LEVEL_1_PLAN: "LEVEL 1 (PLAN): Create plans, courses, and recommendations.",
    AutonomyLevel.LEVEL_2_REVERSIBLE: "LEVEL 2 (REVERSIBLE ACTION): Create notes, generate files, and update local learning progress.",
    AutonomyLevel.LEVEL_3_APPROVAL_REQUIRED: (
        "LEVEL 3 (APPROVAL REQUIRED): Install packages, modify important existing files, change configurations, "
        "connect external accounts, or make paid external API calls."
    ),
    AutonomyLevel.LEVEL_4_EXPLICIT_CONFIRMATION: (
        "LEVEL 4 (EXPLICIT CONFIRMATION REQUIRED): Delete data, overwrite backups, publish repositories, "
        "push Git commits, deploy infrastructure, or perform irreversible external actions."
    ),
}


class AutonomyPermissionError(PermissionError):
    """Raised when an agent or tool attempts an action exceeding its granted autonomy level."""


class AgentLoopError(RuntimeError):
    """Raised when an agent exceeds maximum tool calls or repeats identical tool invocations."""


class AgentCancelledError(RuntimeError):
    """Raised when a running agentic workflow is cancelled or exceeds its deadline."""


class ConflictingInstructionError(ValueError):
    """Raised when conflicting or adversarial instructions are detected in agent tasks."""


@dataclass
class CancellationToken:
    """Thread-safe cancellation and deadline tracker for multi-agent workflows."""

    cancelled: bool = False
    reason: str = ""
    deadline_monotonic: float | None = None

    @classmethod
    def with_timeout(cls, timeout_seconds: float) -> "CancellationToken":
        return cls(deadline_monotonic=time.monotonic() + float(timeout_seconds))

    def cancel(self, reason: str = "User requested cancellation") -> None:
        self.cancelled = True
        self.reason = reason

    def check(self) -> None:
        if self.cancelled:
            raise AgentCancelledError(f"Execution cancelled: {self.reason}")
        if self.deadline_monotonic is not None and time.monotonic() > self.deadline_monotonic:
            raise AgentCancelledError("Execution exceeded configured deadline.")


@dataclass
class ExecutionAuditEntry:
    """Immutable log record of an agent or tool operation."""

    timestamp: str
    actor: str
    operation: str
    required_level: int
    granted_level: int
    status: str
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "actor": self.actor,
            "operation": self.operation,
            "required_level": int(self.required_level),
            "required_level_name": AutonomyLevel(self.required_level).name,
            "granted_level": int(self.granted_level),
            "status": self.status,
            "details": self.details,
        }


class PermissionGuard:
    """Enforces autonomy levels, workspace confinement, loop prevention, and audit logging."""

    def __init__(
        self,
        workspace_root: str | Path,
        max_autonomy_level: AutonomyLevel = AutonomyLevel.LEVEL_2_REVERSIBLE,
        approved_operations: set[str] | None = None,
        confirmed_operations: set[str] | None = None,
        max_tool_calls: int = 40,
        max_duplicate_calls: int = 2,
        cancellation_token: CancellationToken | None = None,
    ) -> None:
        self.workspace_root = Path(workspace_root).resolve()
        self.max_autonomy_level = AutonomyLevel(max_autonomy_level)
        self.approved_operations = set(approved_operations or set())
        self.confirmed_operations = set(confirmed_operations or set())
        self.max_tool_calls = max_tool_calls
        self.max_duplicate_calls = max_duplicate_calls
        self.cancellation_token = cancellation_token or CancellationToken()
        self.audit_log: list[ExecutionAuditEntry] = []
        self._call_counts: dict[str, int] = {}
        self._total_calls: int = 0

    def check_cancellation(self) -> None:
        self.cancellation_token.check()

    def authorize(
        self,
        actor: str,
        operation: str,
        required_level: AutonomyLevel,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """Check whether `actor` may perform `operation` at `required_level`."""
        self.check_cancellation()
        req = AutonomyLevel(required_level)
        now = datetime.now(timezone.utc).isoformat()

        if req == AutonomyLevel.LEVEL_4_EXPLICIT_CONFIRMATION:
            if operation not in self.confirmed_operations and self.max_autonomy_level < AutonomyLevel.LEVEL_4_EXPLICIT_CONFIRMATION:
                self.audit_log.append(
                    ExecutionAuditEntry(
                        timestamp=now,
                        actor=actor,
                        operation=operation,
                        required_level=req,
                        granted_level=self.max_autonomy_level,
                        status="denied_confirmation_required",
                        details=metadata or {},
                    )
                )
                raise AutonomyPermissionError(
                    f"Operation '{operation}' by '{actor}' requires LEVEL 4 Explicit Confirmation "
                    f"(current autonomy level: {self.max_autonomy_level.name})."
                )

        elif req == AutonomyLevel.LEVEL_3_APPROVAL_REQUIRED:
            if operation not in self.approved_operations and operation not in self.confirmed_operations and self.max_autonomy_level < AutonomyLevel.LEVEL_3_APPROVAL_REQUIRED:
                self.audit_log.append(
                    ExecutionAuditEntry(
                        timestamp=now,
                        actor=actor,
                        operation=operation,
                        required_level=req,
                        granted_level=self.max_autonomy_level,
                        status="denied_approval_required",
                        details=metadata or {},
                    )
                )
                raise AutonomyPermissionError(
                    f"Operation '{operation}' by '{actor}' requires LEVEL 3 User Approval "
                    f"(current autonomy level: {self.max_autonomy_level.name})."
                )

        elif req > self.max_autonomy_level:
            self.audit_log.append(
                ExecutionAuditEntry(
                    timestamp=now,
                    actor=actor,
                    operation=operation,
                    required_level=req,
                    granted_level=self.max_autonomy_level,
                    status="denied_insufficient_autonomy",
                    details=metadata or {},
                )
            )
            raise AutonomyPermissionError(
                f"Operation '{operation}' by '{actor}' requires {req.name}, "
                f"which exceeds current max autonomy {self.max_autonomy_level.name}."
            )

        self.audit_log.append(
            ExecutionAuditEntry(
                timestamp=now,
                actor=actor,
                operation=operation,
                required_level=req,
                granted_level=self.max_autonomy_level,
                status="authorized",
                details=metadata or {},
            )
        )
        return True

    def reset_call_counters(self) -> None:
        """Reset per-run loop detection counters at the start of a new orchestrator goal."""
        self._call_counts.clear()
        self._total_calls = 0

    def record_tool_invocation(self, actor: str, tool_name: str, args: dict[str, Any]) -> None:
        """Prevent infinite loops or excessive repeated tool calls with identical arguments."""
        self.check_cancellation()
        self._total_calls += 1
        if self._total_calls > self.max_tool_calls:
            raise AgentLoopError(
                f"Agent '{actor}' exceeded maximum allowed tool calls ({self.max_tool_calls})."
            )

        canonical = json.dumps({"actor": actor, "tool": tool_name, "args": args}, sort_keys=True, default=str)
        sig = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]
        self._call_counts[sig] = self._call_counts.get(sig, 0) + 1
        if self._call_counts[sig] > self.max_duplicate_calls:
            raise AgentLoopError(
                f"Loop detected: Agent '{actor}' invoked tool '{tool_name}' with identical arguments "
                f"more than {self.max_duplicate_calls} times."
            )

    def validate_workspace_file(self, candidate: str | Path) -> Path:
        """Restrict file writes/reads to authorized workspace root."""
        return resolve_safe_workspace_path(self.workspace_root, candidate)

    def validate_external_url(self, url: str) -> str:
        """Validate external URLs against SSRF and local file schemes."""
        return validate_safe_url(url)

    @staticmethod
    def detect_conflicting_instructions(instruction_text: str) -> dict[str, Any]:
        """Detect contradictory directives or embedded prompt-injection attempts."""
        sanitized, warnings = sanitize_untrusted_text(instruction_text)
        lower = instruction_text.lower()
        contradictions: list[str] = []
        if "delete all" in lower and "preserve" in lower:
            contradictions.append("Contradictory directive: simultaneous 'delete all' and 'preserve' instructions.")
        if "skip verification" in lower or "fabricate citation" in lower or "invent url" in lower:
            contradictions.append("Safety conflict: request to skip citation verification or fabricate sources.")
        if "push to assafkip" in lower or "force push" in lower:
            contradictions.append("Repository safety conflict: prohibited upstream push or force-push instruction.")
        return {
            "has_conflict": bool(warnings or contradictions),
            "injection_warnings": warnings,
            "contradictions": contradictions,
            "sanitized_text": sanitized,
        }
