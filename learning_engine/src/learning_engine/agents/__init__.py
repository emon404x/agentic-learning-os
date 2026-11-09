"""Agentic AI Architecture Package (`learning_engine.agents`).

Exports:
- Central Orchestrator (`LearningOrchestrator`, `OrchestrationResult`, `ORCHESTRATOR_STAGES`)
- 10 Specialized Agents (`create_specialized_agent_team`, `SpecializedAgent`, `AgentTask`, `AgentExecutionReport`)
- Autonomy & Permission Controls (`AutonomyLevel`, `PermissionGuard`, `CancellationToken`, `AutonomyPermissionError`, `AgentLoopError`, `AgentCancelledError`)
"""

from .orchestrator import LearningOrchestrator, OrchestrationResult, ORCHESTRATOR_STAGES
from .permissions import (
    AUTONOMY_DESCRIPTIONS,
    AgentCancelledError,
    AgentLoopError,
    AutonomyLevel,
    AutonomyPermissionError,
    CancellationToken,
    ExecutionAuditEntry,
    PermissionGuard,
)
from .specialists import (
    AgentExecutionReport,
    AgentTask,
    AssessmentAgent,
    CurriculumArchitectAgent,
    KnowledgeManagerAgent,
    PersonalTutorAgent,
    PracticalLabAgent,
    ProjectMentorAgent,
    QualityAndSafetyAgent,
    ResearchAgent,
    ResearchPaperAgent,
    RevisionAgent,
    SpecializedAgent,
    create_specialized_agent_team,
)

__all__ = [
    "AUTONOMY_DESCRIPTIONS",
    "AgentCancelledError",
    "AgentExecutionReport",
    "AgentLoopError",
    "AgentTask",
    "AssessmentAgent",
    "AutonomyLevel",
    "AutonomyPermissionError",
    "CancellationToken",
    "CurriculumArchitectAgent",
    "ExecutionAuditEntry",
    "KnowledgeManagerAgent",
    "LearningOrchestrator",
    "ORCHESTRATOR_STAGES",
    "OrchestrationResult",
    "PermissionGuard",
    "PersonalTutorAgent",
    "PracticalLabAgent",
    "ProjectMentorAgent",
    "QualityAndSafetyAgent",
    "ResearchAgent",
    "ResearchPaperAgent",
    "RevisionAgent",
    "SpecializedAgent",
    "create_specialized_agent_team",
]
