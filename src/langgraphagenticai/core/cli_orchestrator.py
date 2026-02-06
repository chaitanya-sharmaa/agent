"""
CLI orchestrator module for managing CLI workflows.
Handles auditor and creator flows.
"""

import logging
import asyncio
import time
from typing import Optional, List

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
            required_probe_prefixes=None,  # Disable early stopping for comprehensive checks
        )

        live_logger.subsection("Generating Assessment Report")
        print("\n📋 GENERATING ASSESSMENT REPORT...")
        self._print_assessment(tool_results, "pre-deploy")
        live_logger.status("Auditor analysis completed")

    async def run_comprehensive_auditor(self) -> None:
        """Execute a comprehensive multi-stage Kubernetes audit with concurrent execution."""
        start_time = time.time()
        
        logger.info("Starting Comprehensive Auditor")
        live_logger.section("COMPREHENSIVE KUBERNETES AUDIT")
        print("\n" + "╔" + "═" * 78 + "╗")
        print("║" + "🔍 COMPREHENSIVE KUBERNETES SECURITY AUDIT".center(78) + "║")
        print("╚" + "═" * 78 + "╝" + "\n")

        # Stage 1: collect namespaces via MCP tool directly (no LLM gating)
        live_logger.subsection("Stage 1: Namespace Discovery")
        print("\n┌─" + "─" * 76 + "┐")
        print("│ 📋 STAGE 1: Namespace Discovery".ljust(78) + "│")
        print("└─" + "─" * 76 + "┘")
        from src.langgraphagenticai.tools.kubernetes_tool import get_tools

        tools = await get_tools()
        tool_map = {t.name: t for t in tools if hasattr(t, "name")}
        kubectl_get = tool_map.get("kubectl_get")
        if not kubectl_get:
            raise RuntimeError("kubectl_get tool not available from MCP server")

        async def _invoke_tool(tool, args: dict):
            try:
                if hasattr(tool, "ainvoke"):
                    return await asyncio.wait_for(tool.ainvoke(args), timeout=30)
                if hasattr(tool, "invoke"):
                    return tool.invoke(args)
                if callable(tool):
                    if asyncio.iscoroutinefunction(tool):
                        return await asyncio.wait_for(tool(**args), timeout=30)
                    return tool(**args)
                raise ValueError("Unsupported tool type for invocation")
            except Exception as e:
                # Gracefully handle missing resource types or MCP execution errors
                msg = str(e)
                if "doesn't have a resource type" in msg or "Failed to get resource" in msg:
                    return {"items": []}
                if "ENOBUFS" in msg:
                    return {"items": []}
                raise

        def _record_output(output, resource_type: str, namespace: Optional[str] = None):
            return {
                "output": output,
                "tool_name": "kubectl_get",
                "tool_call_id": None,
                "resource_type": resource_type,
                "namespace": namespace,
            }

        namespace_output = await _invoke_tool(
            kubectl_get, {"resourceType": "namespaces"}
        )
        stage1_results = [_record_output(namespace_output, "namespaces")]

        namespaces = self._extract_namespaces(stage1_results)
        
        # Debug: show extracted vs total
        logger.info(f"Extracted {len(namespaces)} valid namespaces from stage 1")
        print(f"   ✓ Found {len(namespaces)} valid namespaces for auditing\n")
        
        # Ensure all discovered namespaces have an inventory entry (even if empty)
        for ns in namespaces:
            self.analyzer.namespace_inventory.setdefault(ns, {})

        # Stage 2: Query resources in each namespace
        live_logger.subsection(f"Stage 2: Namespaced Resources ({len(namespaces)} namespaces)")
        print("┌─" + "─" * 76 + "┐")
        print(f"│ 📦 STAGE 2: Querying {len(namespaces)} Namespaces (Concurrent)".ljust(78) + "│")
        print("└─" + "─" * 76 + "┘")

        # Stage 2: query per-namespace and cluster-wide resources
        ns_resource_types = [
            "pods",
            "deployments",
            "daemonsets",
            "statefulsets",
            "rolebindings",
            "networkpolicies",
        ]
        cluster_resource_types = [
            "clusterroles",
            "clusterrolebindings",
            "peerauthentication",
            "authorizationpolicy",
        ]

        all_results = list(stage1_results)

        live_logger.subsection("Collecting Namespace Resources")
        semaphore = asyncio.Semaphore(6)

        async def _fetch_namespaced(resource_type: str, namespace: str):
            async with semaphore:
                output = await _invoke_tool(
                    kubectl_get,
                    {
                        "resourceType": resource_type,
                        "namespace": namespace,
                        "output": "name",
                    },
                )
                return _record_output(output, resource_type, namespace)

        tasks = [
            _fetch_namespaced(resource_type, namespace)
            for namespace in namespaces
            for resource_type in ns_resource_types
        ]
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for res in results:
                if isinstance(res, Exception):
                    continue
                all_results.append(res)

        # Stage 3: Cluster-wide resources
        live_logger.subsection("Stage 3: Cluster-wide Resources")
        print("\n┌─" + "─" * 76 + "┐")
        print("│ 🌐 STAGE 3: Cluster-wide Resources (Concurrent)".ljust(78) + "│")
        print("└─" + "─" * 76 + "┘")

        async def _fetch_cluster(resource_type: str):
            async with semaphore:
                output = await _invoke_tool(
                    kubectl_get,
                    {"resourceType": resource_type, "output": "name"},
                )
                return _record_output(output, resource_type)

        cluster_tasks = [
            _fetch_cluster(resource_type) for resource_type in cluster_resource_types
        ]
        if cluster_tasks:
            results = await asyncio.gather(*cluster_tasks, return_exceptions=True)
            for res in results:
                if isinstance(res, Exception):
                    continue
                all_results.append(res)

        elapsed = time.time() - start_time
        live_logger.subsection("Generating Comprehensive Assessment Report")
        print("\n┌─" + "─" * 76 + "┐")
        print("│ 📊 GENERATING COMPREHENSIVE ASSESSMENT REPORT".ljust(78) + "│")
        print("└─" + "─" * 76 + "┘\n")
        self._print_assessment(all_results, "comprehensive", elapsed)
        live_logger.status(f"Comprehensive analysis completed in {elapsed:.1f}s")

    def _extract_namespaces(self, tool_results: list) -> List[str]:
        """Extract namespace names from tool results."""
        import re
        
        def is_valid_ns_name(name: str) -> bool:
            """Check if string is a valid Kubernetes namespace name."""
            if not isinstance(name, str):
                return False
            # Valid format: lowercase alphanumeric and hyphens, 1-63 chars
            # Also accept single character names like "a", "b", etc. and names ending in alphanumeric
            pattern = r'^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?$'
            return bool(re.match(pattern, name))
        
        namespaces = set()
        invalid_names = set()
        
        for result in tool_results or []:
            if not isinstance(result, dict):
                continue
            output = result.get("output")
            if output is None:
                continue
            parsed = self.analyzer.parse_kubectl_output(output)
            if isinstance(parsed, dict):
                items = parsed.get("items", []) if isinstance(parsed.get("items"), list) else []
                for item in items:
                    if not isinstance(item, dict):
                        continue
                    name = (
                        item.get("metadata", {}).get("name")
                        or item.get("name")
                    )
                    if name:
                        if is_valid_ns_name(name):
                            namespaces.add(name)
                        else:
                            invalid_names.add(name)
                continue

            # Handle raw name output strings: namespace/<name>
            if isinstance(parsed, str):
                lines = [ln.strip() for ln in parsed.splitlines() if ln.strip()]
                for line in lines:
                    if line.startswith("namespace/"):
                        name = line.split("/", 1)[1]
                    else:
                        name = line
                    if is_valid_ns_name(name):
                        namespaces.add(name)
                    else:
                        invalid_names.add(name)
        
        # Debug log
        if invalid_names:
            logger.debug(f"Filtered out {len(invalid_names)} invalid namespace names: {sorted(invalid_names)[:5]}")
        
        return sorted(namespaces)

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
            required_probe_prefixes=None,  # Disable early stopping for comprehensive verification
        )

        self._print_assessment(tool_results, "post-deploy")

    def _print_assessment(self, tool_results: list, phase: str, elapsed_time: float = None) -> None:
        """
        Print the Zero Trust assessment.
        
        Args:
            tool_results: List of tool execution results
            phase: Phase name (pre-deploy or post-deploy)
            elapsed_time: Execution time in seconds (optional)
        """
        if tool_results:
            cleaned = self._filter_valid_results(tool_results)
            if cleaned:
                assessment = self.analyzer.analyze_and_generate_report(cleaned, elapsed_time)
                print(assessment)
            else:
                print(f"\n⚠️  No valid results for assessment ({phase})")
        else:
            print(f"\n⚠️  Auditor found no tool results ({phase})")

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
