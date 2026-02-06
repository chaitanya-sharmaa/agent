from typing_extensions import TypedDict, List, Annotated, Optional, Dict, Any, Set
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


class State(TypedDict):
    """
    Base state for all LangGraph workflows.
    Contains messages and extensible metadata for different use cases.
    """
    messages: Annotated[List[BaseMessage], add_messages]
    # Metadata for tracking workflow execution
    metadata: Dict[str, Any]


class AuditorState(State):
    """
    Extended state for Zero Trust Auditor workflows.
    Tracks security findings, probes, and remediation options.
    """
    # Tool execution results with provenance
    tool_results: Optional[List[Dict[str, Any]]] = None
    # Security findings with risk scores
    risk_findings: Optional[List[Dict[str, Any]]] = None
    # Executed probe keys to avoid re-execution
    executed_probes: Optional[Set[str]] = None
    # Generated remediation templates for findings
    remediation_templates: Optional[Dict[str, str]] = None


class CreatorState(State):
    """
    Extended state for Zero Trust Creator workflows.
    Tracks deployed resources and verification results.
    """
    # Resources deployed in this run
    deployed_resources: Optional[List[Dict[str, Any]]] = None
    # Verification results after deployment
    verification_results: Optional[List[Dict[str, Any]]] = None
    # Helm deployment status
    helm_status: Optional[Dict[str, Any]] = None


class ComprehensiveAuditorState(AuditorState):
    """
    Extended state for Comprehensive Security Auditor.
    Combines auditor state with additional analysis and recommendations.
    """
    # Security recommendations with prioritization
    recommendations: Optional[List[Dict[str, Any]]] = None
    # Compliance status across frameworks (CIS, NIST, etc.)
    compliance_status: Optional[Dict[str, Any]] = None
    # Evidence chain for audit trail
    evidence_chain: Optional[List[Dict[str, Any]]] = None