"""Deprecated synthesizer node.

This module previously provided a dedicated synthesizer to aggregate tool
outputs into a final Zero Trust assessment. The design was simplified to let
the Auditor/Creator flows and the ZeroTrustAnalyzer produce authoritative
assessments directly. This file remains as a small placeholder for clarity
and to avoid breaking legacy imports.

If you rely on synthesis behavior, call ZeroTrustAnalyzer.analyze_and_generate_report
explicitly instead.
"""


def create_synthesizer_node():
    """Return a backward-compatible synthesizer node.

    The node is kept for compatibility with existing tests and flows but is
    considered deprecated; prefer calling ZeroTrustAnalyzer.analyze_and_generate_report
    directly in new code.

    Behavior:
    - Filters out error-like tool outputs (e.g., "Error: Status is not a valid tool...").
    - Aggregates resource names and important signals into a single assessment
      message prefixed with "Zero Trust Security Assessment".
    - Deduplicates repeated identical inputs using an in-state cache at
      `state['tool_results_cache']` (tests pass this list in and expect it to be
      mutated).
    """
    try:
        from langchain_core.messages import ToolMessage
    except Exception:
        # Fallback simple message holder if langchain_core is not available
        class ToolMessage:  # type: ignore
            def __init__(self, content, tool_call_id=None, tool_name=None):
                self.content = content
                self.tool_call_id = tool_call_id
                self.tool_name = tool_name

    def _synth(state: dict):
        msgs = state.get("messages", []) or []
        cache = state.setdefault("tool_results_cache", [])
        workflow_name = state.get("workflow_name", "").lower()

        # For comprehensive auditor, pass through LLM output as-is (don't reformat)
        if "comprehensive" in workflow_name:
            # Just extract the last AI message and return it
            for m in reversed(msgs):
                if hasattr(m, 'content') and m.content:
                    content = str(m.content).strip()
                    if content and not content.lower().startswith("error:"):
                        return {"messages": [m]}
            return {}

        # Extract noteworthy items
        findings = []
        raw_contents = []
        for m in msgs:
            content = getattr(m, "content", None)
            if not content:
                continue
            lc = str(content).strip().lower()
            # Filter error outputs
            if lc.startswith("error:") or "status is not a valid tool" in lc:
                continue
            raw_contents.append(str(content))

            # Try to parse JSON and extract names/kinds
            try:
                import json
                j = json.loads(content)
                items = j.get("items") if isinstance(j, dict) else None
                if items and isinstance(items, list):
                    for it in items:
                        kind = (it.get("kind") or "").lower()
                        meta = it.get("metadata") or {}
                        name = meta.get("name") or ""
                        ns = meta.get("namespace") or ""
                        if name:
                            findings.append(name.lower())
                        if ns and ns.lower() not in findings:
                            findings.append(ns.lower())
                # For PeerAuthentication include mtls mode if present
                if isinstance(j, dict) and j.get("kind", "").lower() == "peerauthentication":
                    spec = j.get("spec", {})
                    mtls = spec.get("mtls") or {}
                    mode = mtls.get("mode")
                    if mode:
                        findings.append(f"mtls:{str(mode).lower()}")
            except Exception:
                # Not JSON; do a simple text search for names
                if "ztunnel" in lc:
                    findings.append("ztunnel")
                if "istio" in lc and "namespace" in lc:
                    findings.append("istio-system")

        # Fall back to any cached raw outputs if no messages were provided
        if not raw_contents:
            for entry in cache:
                if isinstance(entry, dict) and entry.get("output"):
                    raw_contents.append(str(entry.get("output")))
                    try:
                        import json
                        j = json.loads(entry.get("output"))
                        items = j.get("items") if isinstance(j, dict) else None
                        if items and isinstance(items, list):
                            for it in items:
                                name = (it.get("metadata") or {}).get("name") or ""
                                ns = (it.get("metadata") or {}).get("namespace") or ""
                                if name:
                                    findings.append(name.lower())
                                if ns and ns.lower() not in findings:
                                    findings.append(ns.lower())
                    except Exception:
                        continue

        # Create a fingerprint to deduplicate
        fingerprint = "|".join(sorted(set(raw_contents)))
        if fingerprint in cache:
            return {}

        # Nothing to synthesize
        if not findings and not raw_contents:
            return {}

        # Build assessment text
        header = "Zero Trust Security Assessment"
        detail_lines = []
        if findings:
            detail_lines.append("Findings:")
            for f in sorted(set(findings)):
                detail_lines.append(f" - {f}")
        else:
            detail_lines.append("No notable findings extracted from tool outputs.")

        assessment = header + "\n" + "\n".join(detail_lines)

        # Cache this fingerprint
        cache.append(fingerprint)

        return {"messages": [ToolMessage(content=assessment, tool_call_id="", tool_name="synthesizer")]} 

    return _synth