"""
CLI orchestrator module for managing CLI workflows.
Handles auditor and creator flows.
"""

import logging
from typing import Optional

from src.langgraphagenticai.core.graph_executor import GraphExecutor
from src.langgraphagenticai.graph.graph_builder import GraphBuilder
from src.langgraphagenticai.utils.zero_trust_analyzer import ZeroTrustAnalyzer
from src.langgraphagenticai.utils.live_logger import get_live_logger

logger = logging.getLogger(__name__)
live_logger = get_live_logger()


class CLIOrchestrator:
    """Orchestrates CLI execution flows for auditor and creator modes."""

    # Required probe types for auditor checks
    REQUIRED_PROBES = {
        "namespaces",
        "pods",
        "daemonsets",
        "peerauthentication",
        "authorizationpolicy",
        "networkpolicy",
    }

    # Helm chart configuration
    HELM_CHART_URL = (
        "https://rohkum143.github.io/zero-trust-charts/authorization-policy-0.1.0.tgz"
    )
    HELM_RELEASE_NAME = "auth"
    HELM_NAMESPACE = "istio-system"

    def __init__(
        self,
        graph_builder: GraphBuilder,
        executor: GraphExecutor,
        analyzer: ZeroTrustAnalyzer,
    ):
        """
        Initialize the CLI orchestrator.
        
        Args:
            graph_builder: GraphBuilder instance for creating workflows
            executor: GraphExecutor instance for running workflows
            analyzer: ZeroTrustAnalyzer instance for analysis
        """
        self.graph_builder = graph_builder
        self.executor = executor
        self.analyzer = analyzer

    async def run_auditor(self) -> None:
        """Execute the Zero Trust Auditor workflow."""
        logger.info("Starting Zero Trust Auditor")
        live_logger.section("ZERO TRUST AUDITOR")
        live_logger.info("📊 Analyzing your Kubernetes cluster for security compliance...")
        print("\n" + "🔐 ZERO TRUST AUDITOR ".center(70, "="))
        print("📊 Analyzing your Kubernetes cluster for security compliance...\n")

        live_logger.subsection("Gathering Cluster Data")
        auditor_graph = await self.graph_builder.build_auditor_graph()
        user_message = "Execute Zero Trust Auditor checks now. Use available tools as needed to gather cluster data and provide a final assessment."

        live_logger.info("🔍 Running security checks...")
        tool_results, _ = await self.executor.execute_graph(
            auditor_graph,
            user_message,
            max_events=200,
            required_probe_prefixes=self.REQUIRED_PROBES,
        )

        live_logger.subsection("Generating Assessment Report")
        print("\n📋 GENERATING ASSESSMENT REPORT...")
        self._print_assessment(tool_results, "pre-deploy")
        live_logger.status("Auditor analysis completed")

    async def run_creator(self) -> None:
        """Execute the Zero Trust Creator workflow (audit + deploy + verify)."""
        logger.info("Starting Zero Trust Creator")
        live_logger.section("ZERO TRUST CREATOR")
        live_logger.step(1, 3, "Initial Security Audit")
        print("\n" + "🛡️  ZERO TRUST CREATOR ".center(70, "="))
        print("📋 Step 1: Initial Security Audit\n")

        # Step 1: Run initial audit
        await self.run_auditor()

        # Step 2: Deploy Helm chart
        live_logger.step(2, 3, "Deploying Authorization Policies")
        print("\n" + "🚀 Step 2: Deploying Authorization Policies".center(70, "="))
        await self._deploy_helm_chart()

        # Step 3: Verify post-deployment
        live_logger.step(3, 3, "Post-Deployment Verification")
        print("\n" + "✅ Step 3: Post-Deployment Verification".center(70, "="))
        await self._verify_post_deployment()

    async def _deploy_helm_chart(self) -> None:
        """Deploy the authorization policy Helm chart."""
        print("📦 Installing Helm chart: authorization-policy\n")

        creator_graph = await self.graph_builder.build_creator_graph()
        deploy_message = self._get_helm_deploy_message()

        tool_results, _ = await self.executor.execute_graph(
            creator_graph,
            deploy_message,
            max_events=100,
            stop_on_tool_names={"upgrade_helm_chart", "install_helm_chart"},
        )

        if tool_results:
            print("\n✓ Deployment completed successfully")
        else:
            print("\n⚠️  No deployment output detected")

    async def _verify_post_deployment(self) -> None:
        """Verify the cluster state after deployment."""
        print("🔍 Re-running audit to verify changes...\n")

        auditor_graph = await self.graph_builder.build_auditor_graph()
        user_message = "Execute Zero Trust Auditor checks now. Use available tools as needed to gather cluster data and provide a final assessment."

        tool_results, _ = await self.executor.execute_graph(
            auditor_graph,
            user_message,
            max_events=200,
            required_probe_prefixes=self.REQUIRED_PROBES,
        )

        self._print_assessment(tool_results, "post-deploy")

    def _print_assessment(self, tool_results: list, phase: str) -> None:
        """
        Print the Zero Trust assessment.
        
        Args:
            tool_results: List of tool execution results
            phase: Phase name (pre-deploy or post-deploy)
        """
        if tool_results:
            cleaned = self._filter_valid_results(tool_results)
            if cleaned:
                assessment = self.analyzer.analyze_and_generate_report(cleaned)
                print(f"\n--- Zero Trust Auditor Assessment ({phase}) ---")
                print(assessment)
            else:
                print(f"\n--- No valid results for assessment ({phase}) ---")
        else:
            print(f"\n--- Auditor found no tool results ({phase}) ---")

    @staticmethod
    def _filter_valid_results(tool_results: list) -> list:
        """
        Filter out error results from tool results.
        
        Args:
            tool_results: List of tool execution results
            
        Returns:
            Filtered list of valid results
        """
        return [
            r
            for r in tool_results
            if isinstance(r, dict)
            and r.get("output")
            and not (
                str(r.get("output", "")).strip().lower().startswith("error:")
                or "status is not a valid tool"
                in str(r.get("output", "")).lower()
            )
        ]

    @staticmethod
    def _get_helm_deploy_message() -> str:
        """Get the Helm deployment instruction message."""
        return f"""YOU MUST OUTPUT ONLY VALID JSON TOOL CALLS. NO TEXT, NO EXPLANATIONS, NO REASONING, NO MARKDOWN.

Your task is to deploy the Helm chart as release name "{CLIOrchestrator.HELM_RELEASE_NAME}" in namespace "{CLIOrchestrator.HELM_NAMESPACE}".

The chart URL is: {CLIOrchestrator.HELM_CHART_URL}

Always use upgrade_helm_chart — it is idempotent and will not create new revisions if nothing changed.

OUTPUT EXACTLY THIS JSON (copy precisely, do not change anything):

{{"name": "upgrade_helm_chart", "parameters": {{"name": "{CLIOrchestrator.HELM_RELEASE_NAME}", "chart": "{CLIOrchestrator.HELM_CHART_URL}", "namespace": "{CLIOrchestrator.HELM_NAMESPACE}"}}}}

If the above fails with "release not found", then use:

{{"name": "install_helm_chart", "parameters": {{"name": "{CLIOrchestrator.HELM_RELEASE_NAME}", "chart": "{CLIOrchestrator.HELM_CHART_URL}", "namespace": "{CLIOrchestrator.HELM_NAMESPACE}"}}}}

CRITICAL RULES:
- Use "name" parameter with value "{CLIOrchestrator.HELM_RELEASE_NAME}" — never omit it.
- Use absolute chart URL as "chart".
- Do not add repo, values, or any other fields.
- Output only one JSON line.
- After successful deployment, you are done — do not call more tools.

OUTPUT ONLY THE JSON ABOVE."""
