import os
import sys
import json
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.langgraphagenticai.nodes.chatbot_with_Tool_node import ChatbotWithToolNode, PERSISTENT_PROBES_PATH


def test_persistent_probe_suppression_for_augmented_probes(tmp_path, monkeypatch):
    # Prepare a fake persisted probes file that marks istio probes as already executed
    os.makedirs(os.path.dirname(PERSISTENT_PROBES_PATH), exist_ok=True)
    with open(PERSISTENT_PROBES_PATH, "w") as f:
        json.dump(["pods:istio-system", "daemonsets:istio-system"], f)

    node = ChatbotWithToolNode(None, "system prompt")
    # No existing tool_calls; _ensure_auditor_tool_calls would normally add namespaces, istio_pods, istio_daemonsets
    augmented = node._ensure_auditor_tool_calls([])

    # Because pods:istio-system and daemonsets:istio-system were in persisted set, they should not be added
    names = [ (tc.get('name'), tc.get('args')) for tc in augmented ]
    # Ensure namespaces may still be added (since not persisted in our file) but istio probes are not
    assert not any(tc for tc in augmented if tc.get('args', {}).get('resourceType') == 'pods' and tc.get('args', {}).get('namespace') == 'istio-system')
    assert not any(tc for tc in augmented if tc.get('args', {}).get('resourceType') == 'daemonsets' and tc.get('args', {}).get('namespace') == 'istio-system')

    # Cleanup
    try:
        os.remove(PERSISTENT_PROBES_PATH)
    except Exception:
        pass
