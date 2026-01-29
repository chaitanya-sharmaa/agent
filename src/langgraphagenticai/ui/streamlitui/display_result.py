import streamlit as st
from langchain_core.messages import AIMessage, ToolMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from src.langgraphagenticai.utils.zero_trust_analyzer import ZeroTrustAnalyzer
from src.langgraphagenticai.utils.cli_output_formatter import CLIOutputFormatter
from src.langgraphagenticai.config.config_loader import get_config
import json

class DisplayResultStreamlit:

    def __init__(self, graph, usecase):
        self.graph = graph
        self.usecase = usecase
        self.tool_results = []
        self.formatter = CLIOutputFormatter(show_raw_output=False)

    async def display_result_on_ui(self):
        """
        Displays the result of the agentic workflow in the Streamlit UI with live progress.
        """
        st.markdown(f"## 🔐 {self.usecase}")

        # Comprehensive auditor follows the exact flow of test_comprehensive.py
        if "comprehensive" in self.usecase.lower():
            await self._run_comprehensive_workflow()
            return
        
        # Create containers for real-time updates
        status_container = st.container()
        logs_container = st.container()
        tool_output_container = st.container()
        final_result_container = st.container()
        
        # Status and logs placeholders
        with status_container:
            col1, col2, col3 = st.columns(3)
            with col1:
                event_counter = st.empty()
                event_counter.metric("Events", 0)
            with col2:
                tool_counter = st.empty()
                tool_counter.metric("Tools Executed", 0)
            with col3:
                probe_counter = st.empty()
                probe_counter.metric("Probes Collected", 0)
        
        with logs_container:
            st.markdown("### 📊 Live Execution Log")
            log_output = st.empty()
            log_messages = []
        
        # Helper to run a graph and collect tool outputs (non-streaming)
        async def run_graph_and_collect(graph_obj, user_message, max_events=200, stop_on_tool_names=None, required_probe_prefixes=None):
            collected_tool_results = []
            tool_call_map = {}
            executed_probe_keys = set()
            event_count = 0
            
            # Increase recursion limit for comprehensive audits (more tool calls needed)
            recursion_limit = 150 if is_comprehensive else 50

            async for event in graph_obj.astream({"messages": [("human", user_message)]}, {"recursion_limit": recursion_limit}):
                event_count += 1
                
                if event_count > max_events:
                    log_messages.append(f"⚠️  Max events ({max_events}) reached")
                    with log_output:
                        st.code("\n".join(log_messages[-20:]))
                    break

                self.formatter.process_event(event)

                # Map planned tool calls
                if "chatbot" in event and isinstance(event["chatbot"], dict):
                    for msg in event["chatbot"].get("messages", []):
                        tcalls = getattr(msg, "tool_calls", None) or []
                        if tcalls:
                            log_messages.append(f"📝 [Event {event_count}] LLM Planning {len(tcalls)} tool(s)")
                            for tc in tcalls:
                                name = tc.get("name", "?")
                                args = tc.get("args", {})
                                rt = args.get("resourceType", "?")
                                ns = args.get("namespace", "all")
                                log_messages.append(f"   • {name}(resourceType='{rt}', namespace='{ns}')")
                                tc_id = tc.get("id")
                                if tc_id:
                                    tool_call_map[tc_id] = (tc.get("name"), tc.get("args", {}))

                # Collect tool outputs
                if "tools" in event and isinstance(event["tools"], dict):
                    for msg in event["tools"].get("messages", []):
                        content = getattr(msg, "content", None)
                        if not content or not str(content).strip():
                            continue

                        tool_call_id = getattr(msg, "tool_call_id", None)
                        tool_name = getattr(msg, "tool_name", None)
                        
                        # Log execution
                        if "error" in str(content).lower() or "forbidden" in str(content).lower():
                            log_messages.append(f"❌ [Event {event_count}] {tool_name}: ERROR")
                        else:
                            lines = str(content).split("\n")
                            log_messages.append(f"✓ [Event {event_count}] {tool_name}: Got {len(lines)} lines")
                        
                        record = {"output": content, "tool_call_id": tool_call_id, "tool_name": tool_name}
                        self.tool_results.append(record)
                        collected_tool_results.append(record)

                        # Map to planned probe
                        if tool_call_id and tool_call_id in tool_call_map:
                            planned_name, planned_args = tool_call_map.get(tool_call_id, (None, {}))
                            rt = (planned_args or {}).get("resourceType") or (planned_args or {}).get("resource") or ""
                            ns = (planned_args or {}).get("namespace") or ""
                            probe_key = f"{str(rt).lower()}:{ns}" if ns else f"{str(rt).lower()}:"
                            executed_probe_keys.add(probe_key)

                        with tool_output_container:
                            with st.expander(f"Tool Output - {tool_name or getattr(msg, 'tool_name', 'kubectl_get')}", expanded=False):
                                st.code(str(content)[:2000], language="yaml")
                        
                        if stop_on_tool_names and tool_name in stop_on_tool_names:
                            log_messages.append(f"✅ Stopping: {tool_name} executed")
                            with log_output:
                                st.code("\n".join(log_messages[-20:]))
                            return collected_tool_results, executed_probe_keys
                
                # Update metrics and logs every event
                event_counter.metric("Events", event_count)
                tool_counter.metric("Tools Executed", len(collected_tool_results))
                probe_counter.metric("Probes Collected", len(executed_probe_keys))
                
                with log_output:
                    st.code("\n".join(log_messages[-20:]))  # Show last 20 lines

                # Early stop when we've found required probes
                if required_probe_prefixes:
                    probes_found = {p.split(":")[0] for p in executed_probe_keys}
                    if required_probe_prefixes.issubset(probes_found):
                        log_messages.append(f"✅ All required probes executed ({len(executed_probe_keys)} total)")
                        with log_output:
                            st.code("\n".join(log_messages[-20:]))
                        break

            return collected_tool_results, executed_probe_keys

        # Determine which workflow to run based on user selection
        is_comprehensive = "comprehensive" in self.usecase.lower()
        
        # Build appropriate graph
        try:
            model = getattr(self.graph, "_agenticai_model", None)
            if model:
                from src.langgraphagenticai.graph.graph_builder import GraphBuilder
                # Use the selected workflow, not hardcoded auditor
                workflow_name = self.usecase if is_comprehensive else "Zero Trust Auditor"
                result_graph = await GraphBuilder(model).setup_graph(workflow_name)
            else:
                result_graph = self.graph
        except Exception:
            result_graph = self.graph

        # Customize message and display based on workflow type
        if is_comprehensive:
            # Stage 1: Get namespaces
            user_message = "Query all Kubernetes namespaces to get the complete list."
            result_header = "## 🔍 Comprehensive Security Audit - Stage 1: Collecting Namespaces"
            # Don't stop early for comprehensive - we need all the data
            cleaned_prefixes = None
        else:
            user_message = "Execute Zero Trust Auditor checks now. Use available tools as needed to gather cluster data and provide a final assessment."
            result_header = "## Zero Trust Auditor: Pre-deploy Check"
            cleaned_prefixes = {"namespaces", "pods", "daemonsets", "peerauthentication", "authorizationpolicy", "networkpolicy"}

        with final_result_container:
            st.markdown("---")
            st.markdown(result_header)

        audit_tool_results, audit_probes = await run_graph_and_collect(result_graph, user_message, max_events=1000, required_probe_prefixes=cleaned_prefixes)
        
        # If comprehensive, run stage 2 after stage 1
        if is_comprehensive:
            st.markdown("### ✅ Stage 1 Complete - Got Namespaces")
            st.markdown("---")
            st.markdown("## 🔍 Comprehensive Security Audit - Stage 2: Analyzing All Resources")
            
            # Parse namespaces from Stage 1 results
            namespaces = []
            for result in audit_tool_results:
                try:
                    output_data = json.loads(result.get("output", "{}"))
                    if "items" in output_data:
                        for item in output_data["items"]:
                            if item.get("kind") == "Namespace":
                                namespaces.append(item.get("name"))
                except:
                    pass
            
            # Fallback if parsing failed
            if not namespaces:
                namespaces = ["default", "aks-command", "application", "argocd", "cert-manager", "kube-system", 
                             "kube-public", "kube-node-lease", "gen-ai-work-ns", "genai-fe", "falkordb", "marex", 
                             "mcp", "mcpserver", "mock", "mongodb", "neo4j", "persona", "visual", "weaviate", "axa", "lsec"]
            
            st.markdown(f"**Querying 6 resource types for {len(namespaces)} namespaces...**")
            
            # Stage 2: Direct MCP tool calls per resource type to ensure deterministic coverage
            audit_tool_results_stage2 = []
            progress_placeholder = st.empty()
            resource_types = ["pods", "deployments", "daemonsets", "statefulsets", "rolebindings", "networkpolicies"]
            cluster_resources = ["clusterroles", "clusterrolebindings", "peerauthentication", "authorizationpolicy"]
            all_namespaces = namespaces
            total_queries = len(all_namespaces) * len(resource_types) + len(cluster_resources)
            query_count = 0

            # Initialize MCP client and kubectl_get tool
            config = get_config()
            client = MultiServerMCPClient({
                "kubernetes": {
                    "url": config.get_mcp_url(),
                    "transport": config.get_mcp_transport(),
                }
            })
            tools = await client.get_tools()
            kubectl_get_tool = next(t for t in tools if t.name == "kubectl_get")

            # Filter resource types to those supported by the cluster
            available_resources = None
            list_api_tool = next((t for t in tools if t.name == "list_api_resources"), None)
            if list_api_tool:
                try:
                    list_result = await list_api_tool.ainvoke({})
                    raw_text = ""
                    if isinstance(list_result, dict) and "content" in list_result:
                        content = list_result.get("content", "")
                        if isinstance(content, list):
                            parts = []
                            for item in content:
                                if isinstance(item, dict) and "text" in item:
                                    parts.append(str(item.get("text", "")))
                            raw_text = "\n".join(parts) if parts else str(content)
                        else:
                            raw_text = str(content)
                    elif isinstance(list_result, list) and list_result:
                        parts = []
                        for item in list_result:
                            if isinstance(item, dict) and "text" in item:
                                parts.append(str(item.get("text", "")))
                            else:
                                parts.append(str(item))
                        raw_text = "\n".join(parts)
                    else:
                        raw_text = str(list_result)

                    resources = set()
                    for line in raw_text.splitlines():
                        line = line.strip()
                        if not line or line.lower().startswith("name "):
                            continue
                        parts = line.split()
                        if parts:
                            resources.add(parts[0].lower())
                    if resources:
                        available_resources = resources
                except Exception:
                    available_resources = None

            if available_resources:
                resource_types = [rt for rt in resource_types if rt.lower() in available_resources]
                cluster_resources = [rt for rt in cluster_resources if rt.lower() in available_resources]
            
            # Query each namespace for each resource type
            for ns_idx, ns in enumerate(namespaces, 1):
                for rt in resource_types:
                    query_count += 1
                    progress_placeholder.markdown(f"⏳ Query {query_count}/{total_queries}: {rt} in **{ns}** ({ns_idx}/{len(namespaces)} namespaces)")
                    args = {"resourceType": rt, "namespace": ns, "output": "json"}
                    try:
                        result = await kubectl_get_tool.ainvoke(args)
                        audit_tool_results_stage2.append({
                            "tool_name": "kubectl_get",
                            "resourceType": rt,
                            "namespace": ns,
                            "output": result,
                        })
                    except Exception as e:
                        audit_tool_results_stage2.append({
                            "tool_name": "kubectl_get",
                            "resourceType": rt,
                            "namespace": ns,
                            "error": str(e),
                        })
            
            # Query cluster-wide resources
            for cr in cluster_resources:
                query_count += 1
                progress_placeholder.markdown(f"⏳ Query {query_count}/{total_queries}: cluster-wide {cr}")
                args = {"resourceType": cr, "output": "json"}
                try:
                    result = await kubectl_get_tool.ainvoke(args)
                    audit_tool_results_stage2.append({
                        "tool_name": "kubectl_get",
                        "resourceType": cr,
                        "output": result,
                    })
                except Exception as e:
                    audit_tool_results_stage2.append({
                        "tool_name": "kubectl_get",
                        "resourceType": cr,
                        "error": str(e),
                    })
            
            # Combine results from both stages
            audit_tool_results = audit_tool_results + audit_tool_results_stage2
            
            progress_placeholder.markdown(f"### ✅ Stage 2 Complete - Executed {query_count} queries across {len(namespaces)} namespaces")
        else:
            user_message = "Execute Zero Trust Auditor checks now. Use available tools as needed to gather cluster data and provide a final assessment."
            cleaned_prefixes = {"namespaces", "pods", "daemonsets", "peerauthentication", "authorizationpolicy", "networkpolicy"}
        
        result_header = "## 🔍 Comprehensive Security Audit" if is_comprehensive else "## Zero Trust Auditor: Pre-deploy Check"

        with final_result_container:
            st.markdown("---")
            st.markdown(result_header)

        audit_tool_results, audit_probes = await run_graph_and_collect(result_graph, user_message, max_events=1000, required_probe_prefixes=cleaned_prefixes)

        # Display pre-deploy assessment
        with final_result_container:
            if audit_tool_results:
                # Show raw audit tool results for debugging in the UI
                with st.expander("Raw Audit Tool Results (debug)", expanded=False):
                    st.write(f"Total collected (raw): {len(audit_tool_results)}")
                    for i, r in enumerate(audit_tool_results):
                        tool_name = r.get('tool_name') or r.get('name') or 'unknown'
                        tool_call_id = r.get('tool_call_id') or ''
                        out = r.get('output')
                        out_type = type(out).__name__
                        try:
                            display_out = out if isinstance(out, str) else json.dumps(out)
                        except Exception:
                            display_out = str(out)
                        st.markdown(f"**raw #{i}** tool={tool_name} id={tool_call_id} type={out_type}")
                        st.code(display_out if len(str(display_out)) < 1000 else str(display_out)[:1000] + '...', language='yaml')

                    # Also show any formatted results the CLI formatter captured
                    formatted_results = self.formatter.get_tool_results() or []
                    st.write(f"Total formatted (formatter): {len(formatted_results)}")
                    for i, r in enumerate(formatted_results):
                        try:
                            display_out = r.get('output') if isinstance(r, dict) else str(r)
                        except Exception:
                            display_out = str(r)
                        st.markdown(f"**fmt #{i}**")
                        st.code(display_out if len(str(display_out)) < 1000 else str(display_out)[:1000] + '...', language='yaml')

                # Prefer formatter's parsed outputs if available (they extract JSON text from tool content reliably)
                source_for_analysis = formatted_results if formatted_results else audit_tool_results

                # Normalize outputs to strings before analysis so parsing is consistent with CLI
                normalized = []
                for r in source_for_analysis:
                    if not (isinstance(r, dict) and r.get('output')):
                        continue
                    out = r.get('output')
                    if isinstance(out, str):
                        out_text = out
                    else:
                        try:
                            out_text = json.dumps(out)
                        except Exception:
                            out_text = str(out)
                    # Filter obvious errors
                    out_text_lower = out_text.strip().lower()
                    if out_text_lower.startswith('error:') or 'status is not a valid tool' in out_text_lower:
                        continue
                    new_r = {**r, 'output': out_text}
                    normalized.append(new_r)

                st.write(f"[DEBUG] Normalized entries for analysis: {len(normalized)}")

                # For comprehensive audit, display raw LLM output directly
                # For standard auditor, use analyzer to generate formatted assessment
                if is_comprehensive:
                    # Comprehensive workflow - show the LLM's comprehensive analysis report
                    st.markdown("### 📋 Comprehensive Security Audit Report")
                    
                    # The comprehensive audit generates a full report from the LLM
                    # We need to get the final analysis from the last AI message in the graph
                    final_report = None
                    
                    # Look for the final comprehensive report in the last AI response
                    if audit_tool_results:
                        # The last meaningful response should be the analysis
                        # We'll show the collected data summary plus ask for formatted output
                        
                        # First, show resource inventory from collected data
                        if normalized:
                            st.markdown("#### 📊 Cluster Resource Inventory")
                            resource_count = {}
                            namespace_data = {}
                            
                            for entry in normalized:
                                try:
                                    out = entry.get('output', '')
                                    j = json.loads(out) if isinstance(out, str) else out
                                    items = []
                                    if isinstance(j, dict):
                                        items = j.get('items', [])
                                    elif isinstance(j, list):
                                        items = j
                                    
                                    if items:
                                        first_item = items[0] if isinstance(items, list) else items
                                        kind = first_item.get('kind', 'Unknown')
                                        count = len(items) if isinstance(items, list) else 1
                                        resource_count[kind] = resource_count.get(kind, 0) + count
                                        
                                        # Track by namespace
                                        if kind in ['Pod', 'Deployment', 'DaemonSet', 'StatefulSet', 'Role', 'RoleBinding', 'NetworkPolicy']:
                                            for item in (items if isinstance(items, list) else [items]):
                                                ns = item.get('metadata', {}).get('namespace') or item.get('namespace') or 'cluster-wide'
                                                if ns not in namespace_data:
                                                    namespace_data[ns] = {}
                                                namespace_data[ns][kind] = namespace_data[ns].get(kind, 0) + 1
                                except:
                                    pass
                            
                            # Display overall metrics
                            if resource_count:
                                cols = st.columns(min(4, len(resource_count)))
                                for idx, (kind, count) in enumerate(sorted(resource_count.items())):
                                    with cols[idx % len(cols)]:
                                        st.metric(f"{kind}", count)
                            
                            # Display per-namespace breakdown
                            st.markdown("#### 🔍 Per-Namespace Breakdown")
                            for ns in sorted(namespace_data.keys()):
                                with st.expander(f"**{ns}**"):
                                    ns_resources = namespace_data[ns]
                                    cols = st.columns(len(ns_resources))
                                    for idx, (kind, count) in enumerate(sorted(ns_resources.items())):
                                        with cols[idx]:
                                            st.metric(kind, count)
                    
                    # Show raw audit data for reference
                    with st.expander("📋 Raw Audit Data (for reference)"):
                        for i, result in enumerate(audit_tool_results[:10]):  # Show first 10
                            tool_name = result.get('tool_name') or 'unknown'
                            output = result.get('output') or result.get('content', '')
                            
                            if output and ('error' not in str(output).lower() and 'not a valid tool' not in str(output).lower()):
                                st.markdown(f"**{tool_name}**")
                                output_str = output if isinstance(output, str) else json.dumps(output, indent=2)
                                try:
                                    st.code(output_str[:1500], language="json")
                                except:
                                    st.code(output_str[:1500], language="text")
                else:
                    # Standard auditor workflow - use analyzer for formatted assessment
                    analyzer = ZeroTrustAnalyzer()
                    assessment = analyzer.analyze_and_generate_report(normalized)
                    st.code(assessment, language="text")

                    # Summarize evidence similar to CLI: parse normalized outputs for common resources
                    namespaces = set()
                    istio_pods = []
                    istiod_pods = []
                    ztunnel_daemonsets = []
                    peerauth_ns = set()
                    netpol_ns = set()

                    for entry in normalized:
                        out = entry.get('output')
                        # Try JSON parse and handle both dict and list shapes
                        try:
                            j = json.loads(out) if isinstance(out, str) else out
                            items = []
                            if isinstance(j, dict):
                                items = j.get('items') or ([j] if j.get('kind') else [])
                            elif isinstance(j, list):
                                items = j

                            for it in items:
                                if not isinstance(it, dict):
                                    continue
                                kind = (it.get('kind') or '').lower()
                                meta = it.get('metadata') or {}
                                name = meta.get('name') or it.get('name')
                                ns = meta.get('namespace') or it.get('namespace')
                                if kind == 'namespace' and name:
                                    namespaces.add(name)
                                if kind == 'pod' and name:
                                    if ns:
                                        istio_pods.append(f"{name} ({ns})")
                                        if 'istiod' in (name or '').lower():
                                            istiod_pods.append(f"{name} ({ns})")
                                if kind == 'daemonset' and name:
                                    if 'ztunnel' in (name or '').lower():
                                        ztunnel_daemonsets.append(name)
                                if kind == 'peerauthentication' and ns:
                                    peerauth_ns.add(ns)
                                if kind == 'networkpolicy' and ns:
                                    netpol_ns.add(ns)
                        except Exception:
                            # Simple text searches if not JSON
                            txt = str(out).lower()
                            if 'istio' in txt and 'namespace' in txt:
                                namespaces.add('istio-system')
                            if 'ztunnel' in txt:
                                ztunnel_daemonsets.append('ztunnel')

                    # Show evidence block
                    st.markdown('**Evidence:**')
                    if namespaces:
                        st.write(f"Namespaces found: {', '.join(sorted(namespaces))}")
                    if istio_pods:
                        st.write(f"Istio-related pods: {', '.join(istio_pods)}")
                    if istiod_pods:
                        st.write(f"Istiod pods: {', '.join(istiod_pods)}")
                    if ztunnel_daemonsets:
                        st.write(f"ztunnel daemonsets: {', '.join(sorted(set(ztunnel_daemonsets)))}")
                    if peerauth_ns:
                        st.write(f"PeerAuthentication namespaces: {', '.join(sorted(peerauth_ns))}")
                    if netpol_ns:
                        st.write(f"NetworkPolicy namespaces: {', '.join(sorted(netpol_ns))}")
            else:
                st.info("Auditor found no tool results for pre-deploy check.")

        if "Zero Trust Creator" in self.usecase:
            creator_deploy_message = '''YOU MUST OUTPUT ONLY VALID JSON TOOL CALLS. NO TEXT, NO EXPLANATIONS, NO REASONING, NO MARKDOWN.

Your task is to deploy the Helm chart as release name "auth" in namespace "istio-system".

The chart URL is: https://rohkum143.github.io/zero-trust-charts/authorization-policy-0.1.0.tgz

Always use upgrade_helm_chart — it is idempotent and will not create new revisions if nothing changed.

OUTPUT EXACTLY THIS JSON (copy precisely, do not change anything):

{"name": "upgrade_helm_chart", "parameters": {"name": "auth", "chart": "https://rohkum143.github.io/zero-trust-charts/authorization-policy-0.1.0.tgz", "namespace": "istio-system"}}

If the above fails with "release not found", then use:

{"name": "install_helm_chart", "parameters": {"name": "auth", "chart": "https://rohkum143.github.io/zero-trust-charts/authorization-policy-0.1.0.tgz", "namespace": "istio-system"}}

CRITICAL RULES:
- Use "name" parameter with value "auth" — never omit it.
- Use absolute chart URL as "chart".
- Do not add repo, values, or any other fields.
- Output only one JSON line.
- After successful deployment, you are done — do not call more tools.

OUTPUT ONLY THE JSON ABOVE.'''

            # Run creator graph (use model-attached compiled graph if available so creators and auditors share model)
            try:
                from src.langgraphagenticai.graph.graph_builder import GraphBuilder
                creator_graph = await GraphBuilder(model).setup_graph("Zero Trust Creator") if model else self.graph
            except Exception:
                creator_graph = self.graph

            deploy_tool_results, deploy_probes = await run_graph_and_collect(creator_graph, creator_deploy_message, max_events=100, stop_on_tool_names={"upgrade_helm_chart", "install_helm_chart"})

            with final_result_container:
                st.markdown("---")
                st.markdown("## Creator: Deploy Results")
                if deploy_tool_results:
                    for r in deploy_tool_results:
                        st.write(r)
                else:
                    st.info("No deploy tool output detected. Check the model/Tool bindings.")

            # Post-deploy verification
            with final_result_container:
                st.markdown("---")
                st.markdown("## Zero Trust Auditor: Post-deploy Verification")

            audit_tool_results_post, audit_probes_post = await run_graph_and_collect(auditor_graph, user_message, max_events=200, required_probe_prefixes=cleaned_prefixes)
            with final_result_container:
                if audit_tool_results_post:
                    cleaned_post = [r for r in audit_tool_results_post if isinstance(r, dict) and r.get('output') and not (str(r.get('output')).strip().lower().startswith('error:') or 'status is not a valid tool' in str(r.get('output')).lower())]
                    analyzer = ZeroTrustAnalyzer()
                    assessment_post = analyzer.analyze_and_generate_report(cleaned_post)
                    st.code(assessment_post, language="text")
                else:
                    st.info("Post-deploy Auditor found no tool results.")

        # Complete and show final results
        with final_result_container:
            st.markdown("---")
            st.success("✅ Analysis complete!")

        final_tool_results = self.formatter.get_tool_results() or self.tool_results
        if final_tool_results or self.tool_results:
            raw_json = json.dumps(final_tool_results if final_tool_results else self.tool_results, indent=2)
            cleaned_json = json.dumps([r for r in (final_tool_results if final_tool_results else self.tool_results) if isinstance(r, dict) and r.get('output') and not (str(r.get('output')).strip().lower().startswith('error:') or 'status is not a valid tool' in str(r.get('output')).lower())], indent=2)

            with final_result_container:
                st.download_button(
                    label="Download Cleaned Results (used for analysis)",
                    data=cleaned_json,
                    file_name=f"{self.usecase.replace(' ', '_')}_cleaned_results.json",
                    mime="application/json")

                st.download_button(
                    label="Download Raw Results (includes errors)",
                    data=raw_json,
                    file_name=f"{self.usecase.replace(' ', '_')}_raw_results.json",
                    mime="application/json")

    async def _run_comprehensive_workflow(self):
        """Run the comprehensive audit in Streamlit using the exact logic from test_comprehensive.py."""
        st.markdown("### STAGE 1: Getting all namespaces")

        model = getattr(self.graph, "_agenticai_model", None)
        if not model:
            st.error("LLM model missing for comprehensive audit.")
            return

        from src.langgraphagenticai.graph.graph_builder import GraphBuilder

        stage1_graph = await GraphBuilder(model).setup_graph("Comprehensive Security Auditor")
        stage1_input = {"messages": [("user", "Query all Kubernetes namespaces to get the complete list.")]}

        stage1_results = []
        log_lines = []
        stage1_log = st.empty()
        tool_call_count = 0

        async for event in stage1_graph.astream(stage1_input):
            for node_name, node_output in event.items():
                log_lines.append(f"[{node_name}]")
                if node_name == "chatbot":
                    messages = node_output.get("messages", [])
                    for msg in messages:
                        if hasattr(msg, "tool_calls") and msg.tool_calls:
                            log_lines.append(f"  Tool calls: {len(msg.tool_calls)}")
                            for tc in msg.tool_calls:
                                log_lines.append(f"    - {tc.get('name', 'unknown')}: {tc.get('args', {})}")
                elif node_name == "tools":
                    for message in node_output.get("messages", []):
                        if hasattr(message, "content"):
                            content = message.content
                            if isinstance(content, list):
                                for item in content:
                                    if isinstance(item, dict) and item.get('type') == 'text':
                                        text_content = item.get('text', '')
                                        stage1_results.append(text_content)
                                        log_lines.append(f"  Tool result: {text_content[:200]}...")
                            elif isinstance(content, str):
                                stage1_results.append(content)
                                log_lines.append(f"  Tool result: {content[:200]}...")
                            tool_call_count += 1

            stage1_log.code("\n".join(log_lines[-40:]), language="text")
            
            # Stop after first tool execution (we only need namespaces)
            if tool_call_count > 0:
                break

        namespaces = []
        for result in stage1_results:
            try:
                data = json.loads(result)
                if "items" in data:
                    for item in data["items"]:
                        if item.get("kind") == "Namespace":
                            ns_name = item.get("name")
                            namespaces.append(ns_name)
            except Exception:
                continue

        st.success(f"Stage 1 Complete: Found {len(namespaces)} namespaces")

        st.markdown("---")
        st.markdown("### STAGE 2: Querying each resource type individually (direct MCP)")

        resource_types = [
            "pods",
            "deployments",
            "daemonsets",
            "statefulsets",
            "rolebindings",
            "networkpolicies",
            "services",
            "ingresses",
            "virtualservices",
            "destinationrules",
            "gateways",
            "configmaps",
        ]
        cluster_resource_types = ["clusterroles", "clusterrolebindings", "peerauthentication", "authorizationpolicy"]
        all_namespaces = namespaces
        total_queries = 0
        stage2_results = []
        namespace_resources = {}
        cluster_resources = {crt: {"count": 0, "items": []} for crt in cluster_resource_types}
        progress_placeholder = st.empty()

        config = get_config()
        client = MultiServerMCPClient({
            "kubernetes": {
                "url": config.get_mcp_url(),
                "transport": config.get_mcp_transport(),
            }
        })
        tools = await client.get_tools()
        kubectl_get_tool = next(t for t in tools if t.name == "kubectl_get")

        # Filter resource types to those supported by the cluster
        available_resources = None
        list_api_tool = next((t for t in tools if t.name == "list_api_resources"), None)
        if list_api_tool:
            try:
                list_result = await list_api_tool.ainvoke({})
                raw_text = ""
                if isinstance(list_result, dict) and "content" in list_result:
                    content = list_result.get("content", "")
                    if isinstance(content, list):
                        parts = []
                        for item in content:
                            if isinstance(item, dict) and "text" in item:
                                parts.append(str(item.get("text", "")))
                        raw_text = "\n".join(parts) if parts else str(content)
                    else:
                        raw_text = str(content)
                elif isinstance(list_result, list) and list_result:
                    parts = []
                    for item in list_result:
                        if isinstance(item, dict) and "text" in item:
                            parts.append(str(item.get("text", "")))
                        else:
                            parts.append(str(item))
                    raw_text = "\n".join(parts)
                else:
                    raw_text = str(list_result)

                resources = set()
                for line in raw_text.splitlines():
                    line = line.strip()
                    if not line or line.lower().startswith("name "):
                        continue
                    parts = line.split()
                    if parts:
                        resources.add(parts[0].lower())
                if resources:
                    available_resources = resources
            except Exception:
                available_resources = None

        if available_resources:
            resource_types = [rt for rt in resource_types if rt.lower() in available_resources]
            cluster_resource_types = [rt for rt in cluster_resource_types if rt.lower() in available_resources]

        for ns_idx, ns in enumerate(all_namespaces, 1):
            progress_placeholder.markdown(f"Processing namespace {ns_idx}/{len(all_namespaces)}: **{ns}**")
            ns_query_count = 0
            ns_tool_calls = []
            ns_results = {}

            namespace_resources[ns] = {
                "pods": {"count": 0, "items": []},
                "deployments": {"count": 0, "items": []},
                "daemonsets": {"count": 0, "items": []},
                "statefulsets": {"count": 0, "items": []},
                "rolebindings": {"count": 0, "items": []},
                "networkpolicies": {"count": 0, "items": []},
                "services": {"count": 0, "items": []},
                "ingresses": {"count": 0, "items": []},
                "virtualservices": {"count": 0, "items": []},
                "destinationrules": {"count": 0, "items": []},
                "gateways": {"count": 0, "items": []},
                "configmaps": {"count": 0, "items": []},
            }

            for rt in resource_types:
                args = {"resourceType": rt, "namespace": ns, "output": "json"}
                ns_query_count += 1
                total_queries += 1
                try:
                    result = await kubectl_get_tool.ainvoke(args)
                    ns_tool_calls.append(f"kubectl_get({rt})")
                    ns_results[rt] = result

                    parsed = None
                    if isinstance(result, list) and len(result) > 0 and isinstance(result[0], dict):
                        if "text" in result[0]:
                            parsed = json.loads(result[0]["text"])

                    if parsed and isinstance(parsed, dict) and "items" in parsed:
                        items = parsed.get("items", [])
                        namespace_resources[ns][rt]["count"] = len(items)
                        namespace_resources[ns][rt]["items"] = items

                    if isinstance(result, dict) and "content" in result:
                        stage2_results.append(result["content"])
                    else:
                        stage2_results.append(str(result))
                except Exception as e:
                    ns_tool_calls.append(f"kubectl_get({rt}) [error: {e}]")
                    ns_results[rt] = {"error": str(e)}

            st.write(f"✅ Executed {ns_query_count} queries for {ns}")
            st.write(f"Tool calls: {', '.join(ns_tool_calls)}")

            st.markdown(f"**Resources in {ns}:**")
            for rt in resource_types:
                st.markdown(f"* {rt.upper()}: ")
                result_data = ns_results.get(rt)
                try:
                    if isinstance(result_data, list) and len(result_data) > 0 and isinstance(result_data[0], dict):
                        if "text" in result_data[0]:
                            result_data = json.loads(result_data[0]["text"])
                        elif "type" in result_data[0] and result_data[0]["type"] == "text":
                            result_data = json.loads(result_data[0].get("text", "{}"))
                    elif isinstance(result_data, str):
                        result_data = json.loads(result_data)
                    elif isinstance(result_data, dict) and "content" in result_data:
                        content = result_data["content"]
                        if isinstance(content, str):
                            result_data = json.loads(content)
                        elif isinstance(content, list) and len(content) > 0:
                            if isinstance(content[0], dict) and "text" in content[0]:
                                result_data = json.loads(content[0]["text"])
                            else:
                                result_data = content[0]
                        else:
                            result_data = content

                    if isinstance(result_data, dict) and "items" in result_data:
                        items = result_data["items"]
                        if items:
                            st.write(f"  ✓ Found {len(items)} {rt}")
                            for item in items[:2]:
                                name = item.get("name", "unknown")
                                st.write(f"    - {name}")
                        else:
                            st.write(f"  No {rt} found")
                    else:
                        st.write(f"  Result: {str(result_data)[:80]}")
                except Exception as e:
                    st.write(f"  Error parsing: {str(e)[:60]}")

        st.success(f"Stage 2 Complete: Executed {total_queries} total queries")

        # Cluster-wide resources
        for crt in cluster_resource_types:
            try:
                args = {"resourceType": crt, "output": "json"}
                total_queries += 1
                result = await kubectl_get_tool.ainvoke(args)
                parsed = None
                if isinstance(result, list) and len(result) > 0 and isinstance(result[0], dict) and "text" in result[0]:
                    parsed = json.loads(result[0]["text"])
                if parsed and isinstance(parsed, dict) and "items" in parsed:
                    items = parsed.get("items", [])
                    cluster_resources[crt]["count"] = len(items)
                    cluster_resources[crt]["items"] = items
            except Exception as e:
                cluster_resources[crt]["error"] = str(e)

        st.markdown("---")
        st.markdown("### COMPREHENSIVE SECURITY AUDIT ANALYSIS")

        # Helper functions for per-namespace analysis
        def add_finding_local(findings_dict, level: str, text: str, standards: str = ""):
            suffix = f" [{standards}]" if standards else ""
            findings_dict[level].append(f"{text}{suffix}")

        def check_workload_list_local(items, ns_name, kind_label, findings_dict):
            standards_priv = "NIST CM-7, CIS 5.2.x"
            for wk in items[:3]:
                spec = wk.get("spec", {}) if isinstance(wk, dict) else {}
                tpl = spec.get("template", {}).get("spec", {}) if isinstance(spec.get("template"), dict) else spec
                sc = tpl.get("securityContext", {}) if isinstance(tpl, dict) else {}
                if tpl.get("hostNetwork"):
                    add_finding_local(findings_dict, "medium_risk", f"{kind_label} uses hostNetwork", standards_priv)
                if sc:
                    if sc.get("runAsUser") in (0, "0") or sc.get("runAsNonRoot") is False:
                        add_finding_local(findings_dict, "medium_risk", f"{kind_label} runs as root", standards_priv)
                    if sc.get("privileged"):
                        add_finding_local(findings_dict, "high_risk", f"{kind_label} is privileged", standards_priv)
                for c in tpl.get("containers", []) if isinstance(tpl.get("containers"), list) else []:
                    csc = c.get("securityContext", {}) if isinstance(c, dict) else {}
                    if csc.get("privileged"):
                        add_finding_local(findings_dict, "high_risk", "Container privileged", standards_priv)
                    if csc.get("allowPrivilegeEscalation") is True:
                        add_finding_local(findings_dict, "medium_risk", "Container allows privilege escalation", standards_priv)
                    img = c.get("image") if isinstance(c, dict) else None
                    if img and ":latest" in img:
                        add_finding_local(findings_dict, "low_risk", "Container uses latest tag", "NIST CM-8")

        standards_netpol = "NIST AC-4, CIS 5.x, NSA/CISA Segmentation"
        standards_mtls = "NIST SC-8/SC-13, CIS 5.1.6, NSA/CISA mTLS"
        standards_ingress = "NIST AC-4, CIS 5.x"

        for ns in all_namespaces:
            st.markdown(f"#### 📦 NAMESPACE: {ns.upper()}")
            resources = namespace_resources[ns]

            table_rows = []
            for rt in resource_types:
                count = resources[rt]["count"]
                status = "✓ Found" if count > 0 else "○ Empty"
                table_rows.append({"Resource Type": rt, "Count": count, "Status": status})
            st.table(table_rows)

            for rt in resource_types:
                items = resources[rt]["items"]
                if items:
                    st.markdown(f"**{rt.upper()} ({len(items)} found):**")
                    for item in items[:5]:
                        # Handle both dict and potentially nested structures
                        if isinstance(item, dict):
                            name = item.get("name") or item.get("metadata", {}).get("name", "unknown")
                        else:
                            name = "unknown"
                        
                        # Extract status based on resource type
                        status_obj = item.get("status", {}) if isinstance(item, dict) else {}
                        status = "Active"  # Default to Active for resources that exist
                        
                        if rt == "pods":
                            if isinstance(status_obj, dict):
                                status = status_obj.get("phase", "Active")
                        elif rt == "deployments":
                            if isinstance(status_obj, dict):
                                ready = status_obj.get("readyReplicas", 0)
                                desired = status_obj.get("replicas", 0)
                                if desired > 0:
                                    status = f"{ready}/{desired} Ready"
                                else:
                                    status = "Pending"
                        elif rt == "statefulsets":
                            if isinstance(status_obj, dict):
                                ready = status_obj.get("readyReplicas", 0)
                                desired = status_obj.get("replicas", 0)
                                if desired > 0:
                                    status = f"{ready}/{desired} Ready"
                                else:
                                    status = "Pending"
                        elif rt in ["rolebindings", "networkpolicies"]:
                            status = "Applied"
                        elif rt == "daemonsets":
                            if isinstance(status_obj, dict):
                                ready = status_obj.get("numberReady", 0)
                                desired = status_obj.get("desiredNumberScheduled", 0)
                                if desired > 0:
                                    status = f"{ready}/{desired} Ready"
                                else:
                                    status = "Pending"
                        
                        st.write(f"✓ {name} [Status: {status}]")
                    if len(items) > 5:
                        st.write(f"... and {len(items) - 5} more")

            # Per-namespace security assessment
            ns_findings = {
                "high_risk": [],
                "medium_risk": [],
                "low_risk": [],
                "suggestions": []
            }

            # NetworkPolicy coverage
            if resources.get("pods", {}).get("count", 0) > 0 and resources.get("networkpolicies", {}).get("count", 0) == 0:
                add_finding_local(ns_findings, "high_risk", "Namespace has workloads but NO NetworkPolicies", standards_netpol)
                ns_findings["suggestions"].append("• Add default-deny ingress/egress NetworkPolicies")

            # Services / Ingress exposure
            for svc in resources.get("services", {}).get("items", [])[:3]:
                svc_type = (svc.get("spec", {}) or {}).get("type") if isinstance(svc, dict) else None
                if svc_type in {"LoadBalancer", "NodePort"} and resources.get("networkpolicies", {}).get("count", 0) == 0:
                    add_finding_local(ns_findings, "medium_risk", f"Service {svc.get('name','unknown')} is {svc_type} without NetworkPolicy", standards_ingress)
            
            for ing in resources.get("ingresses", {}).get("items", [])[:3]:
                tls = (ing.get("spec", {}) or {}).get("tls") if isinstance(ing, dict) else None
                hosts = (ing.get("spec", {}) or {}).get("rules") if isinstance(ing, dict) else None
                if not tls:
                    add_finding_local(ns_findings, "medium_risk", "Ingress missing TLS", standards_ingress)
                if hosts:
                    for rule in hosts:
                        host = rule.get("host") if isinstance(rule, dict) else None
                        if host and host in {"*", "0.0.0.0/0"}:
                            add_finding_local(ns_findings, "medium_risk", "Ingress uses wildcard host", standards_ingress)
                            break

            # Istio VirtualService/DestinationRule/Gateway
            for vs in resources.get("virtualservices", {}).get("items", [])[:3]:
                hosts = vs.get("spec", {}).get("hosts") if isinstance(vs, dict) else None
                if hosts and any(h == "*" for h in hosts):
                    add_finding_local(ns_findings, "medium_risk", "VirtualService allows wildcard hosts", "NIST SC-7, NSA/CISA")
            
            for dr in resources.get("destinationrules", {}).get("items", [])[:3]:
                tls = dr.get("spec", {}).get("trafficPolicy", {}).get("tls") if isinstance(dr, dict) else None
                if tls is None:
                    add_finding_local(ns_findings, "low_risk", "DestinationRule lacks TLS settings", standards_mtls)
            
            for gw in resources.get("gateways", {}).get("items", [])[:3]:
                servers = gw.get("spec", {}).get("servers") if isinstance(gw, dict) else None
                if servers:
                    for srv in servers:
                        if not srv.get("tls"):
                            add_finding_local(ns_findings, "medium_risk", "Gateway server missing TLS", standards_mtls)
                            break

            # Workload security contexts
            check_workload_list_local(resources.get("pods", {}).get("items", []), ns, "Pod", ns_findings)
            check_workload_list_local(resources.get("deployments", {}).get("items", []), ns, "Deployment", ns_findings)
            check_workload_list_local(resources.get("daemonsets", {}).get("items", []), ns, "DaemonSet", ns_findings)
            check_workload_list_local(resources.get("statefulsets", {}).get("items", []), ns, "StatefulSet", ns_findings)

            # Display namespace findings
            if ns_findings["high_risk"] or ns_findings["medium_risk"] or ns_findings["low_risk"]:
                st.markdown("**🔒 SECURITY FINDINGS:**")
                
                if ns_findings["high_risk"]:
                    st.markdown("**🔴 HIGH RISK:**")
                    for finding in ns_findings["high_risk"]:
                        st.write(f"- {finding}")
                
                if ns_findings["medium_risk"]:
                    st.markdown("**🟠 MEDIUM RISK:**")
                    for finding in ns_findings["medium_risk"]:
                        st.write(f"- {finding}")
                
                if ns_findings["low_risk"]:
                    st.markdown("**🟡 LOW RISK:**")
                    for finding in ns_findings["low_risk"]:
                        st.write(f"- {finding}")

                if ns_findings["suggestions"]:
                    st.markdown("**💡 RECOMMENDATIONS:**")
                    for suggestion in ns_findings["suggestions"]:
                        st.write(f"- {suggestion}")

            st.markdown("---")

        st.markdown("### 🔒 CLUSTER-WIDE SECURITY ASSESSMENT")

        # Cluster-wide security findings only
        cluster_findings = {
            "high_risk": [],
            "medium_risk": [],
            "low_risk": [],
            "suggestions": []
        }

        def add_cluster_finding(level: str, text: str, standards: str = ""):
            suffix = f" [{standards}]" if standards else ""
            cluster_findings[level].append(f"{text}{suffix}")

        standards_mtls = "NIST SC-8/SC-13, CIS 5.1.6, NSA/CISA mTLS"
        standards_rbac = "NIST AC-3, CIS 1.x/2.x"

        total_pods = sum(r["pods"]["count"] for r in namespace_resources.values())
        total_deployments = sum(r["deployments"]["count"] for r in namespace_resources.values())
        total_daemonsets = sum(r["daemonsets"]["count"] for r in namespace_resources.values())
        total_statefulsets = sum(r["statefulsets"]["count"] for r in namespace_resources.values())
        total_rolebindings = sum(r["rolebindings"]["count"] for r in namespace_resources.values())
        total_networkpolicies = sum(r["networkpolicies"]["count"] for r in namespace_resources.values())

        peer_items = cluster_resources.get("peerauthentication", {}).get("items", [])
        if not peer_items:
            add_cluster_finding("high_risk", "No PeerAuthentication found (mTLS likely not enforced)", standards_mtls)
            cluster_findings["suggestions"].append("• Enforce STRICT mTLS mesh-wide via PeerAuthentication")
        else:
            for pa in peer_items:
                mode = pa.get("spec", {}).get("mtls", {}).get("mode") if isinstance(pa.get("spec"), dict) else None
                if mode and str(mode).lower() == "permissive":
                    add_cluster_finding("medium_risk", "PeerAuthentication set to PERMISSIVE", standards_mtls)
                    cluster_findings["suggestions"].append("• Set PeerAuthentication mtls.mode to STRICT")
                    break

        authz_items = cluster_resources.get("authorizationpolicy", {}).get("items", [])
        if not authz_items:
            add_cluster_finding("medium_risk", "No AuthorizationPolicy found (no authZ restrictions)", "NIST AC-3, CIS 5.x")
            cluster_findings["suggestions"].append("• Add AuthorizationPolicy to restrict service-to-service access")

        crb_items = cluster_resources.get("clusterrolebindings", {}).get("items", [])
        for crb in crb_items:
            role_ref = (crb.get("roleRef", {}) or {}).get("name") if isinstance(crb, dict) else None
            if role_ref and "cluster-admin" in role_ref:
                add_cluster_finding("high_risk", "ClusterRoleBinding grants cluster-admin", standards_rbac)
                cluster_findings["suggestions"].append("• Limit cluster-admin bindings; use namespace-scoped roles")
                break

        cluster_findings["suggestions"].append("• Enable Pod Security Standards (PSS/PSA) enforcing baseline/restricted")
        cluster_findings["suggestions"].append("• Implement admission controls (OPA/Gatekeeper/Kyverno)")
        cluster_findings["suggestions"].append("• Enable audit logging for all API calls")
        cluster_findings["suggestions"].append("• Use ImagePullSecrets and pinned image tags")

        st.markdown("**Resource Inventory:**")
        st.write(f"Total Pods: {total_pods}")
        st.write(f"Total Deployments: {total_deployments}")
        st.write(f"Total DaemonSets: {total_daemonsets}")
        st.write(f"Total StatefulSets: {total_statefulsets}")
        st.write(f"Total RoleBindings: {total_rolebindings}")
        st.write(f"Total NetworkPolicies: {total_networkpolicies}")

        if cluster_findings["high_risk"]:
            st.markdown("**🔴 HIGH RISK FINDINGS:**")
            for finding in cluster_findings["high_risk"]:
                st.write(f"- {finding}")

        if cluster_findings["medium_risk"]:
            st.markdown("**🟠 MEDIUM RISK FINDINGS:**")
            for finding in cluster_findings["medium_risk"]:
                st.write(f"- {finding}")

        if cluster_findings["low_risk"]:
            st.markdown("**🟡 LOW RISK FINDINGS:**")
            for finding in cluster_findings["low_risk"]:
                st.write(f"- {finding}")

        st.markdown("**💡 RECOMMENDATIONS:**")
        for suggestion in cluster_findings["suggestions"]:
            st.write(f"- {suggestion}")

        st.markdown("---")
        st.markdown("### SUMMARY")
        st.write(f"Namespaces found: {len(namespaces)}")
        expected_queries = len(namespace_resources) * len(resource_types) + len(cluster_resource_types)
        st.write(f"Namespaces queried: {len(namespace_resources)}")
        st.write(f"Resource types per namespace: {len(resource_types)}")
        st.write(f"Expected total queries: {expected_queries}")
        st.write(f"Actual queries executed: {total_queries}")

        if total_queries >= expected_queries:
            st.success("SUCCESS: All expected queries executed!")
        else:
            missing = expected_queries - total_queries
            st.error(f"ISSUE: Missing {missing} queries. Check the Stage 2 prompt and execution logic (some tool calls may have failed).")
