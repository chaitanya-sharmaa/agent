#!/usr/bin/env python3
import asyncio
from src.langgraphagenticai.tools.kubernetes_tool import get_tools
from src.langgraphagenticai.utils.zero_trust_analyzer import ZeroTrustAnalyzer

async def test_ns_extraction():
    tools = await get_tools()
    tool_map = {t.name: t for t in tools if hasattr(t, "name")}
    kubectl_get = tool_map.get("kubectl_get")
    
    if not kubectl_get:
        print("kubectl_get tool not found")
        return
    
    try:
        result = await kubectl_get.ainvoke({"resourceType": "namespaces"})
        print("Raw kubectl_get result:")
        print(f"Type: {type(result)}")
        if isinstance(result, list) and result:
            print(f"First item type: {type(result[0])}")
            if isinstance(result[0], dict):
                print(f"First item keys: {result[0].keys()}")
                text = result[0].get('text', '')
                print(f"Text preview (first 200 chars):\n{text[:200]}")
        elif isinstance(result, str):
            print(f"String preview (first 200 chars):\n{result[:200]}")
        
        # Now parse it
        analyzer = ZeroTrustAnalyzer()
        parsed = analyzer.parse_kubectl_output(result)
        print("\nParsed output:")
        print(f"Type: {type(parsed)}")
        if isinstance(parsed, dict):
            print(f"Keys: {list(parsed.keys())}")
            if 'items' in parsed:
                items = parsed.get('items', [])
                print(f"Items count: {len(items)}")
                if items:
                    print("\nFirst 5 items:")
                    for i, item in enumerate(items[:5]):
                        if isinstance(item, dict):
                            print(f"  [{i}] name={item.get('metadata', {}).get('name') or item.get('name')}")
                    print("\nAll item names:")
                    names = []
                    for item in items:
                        if isinstance(item, dict):
                            name = item.get('metadata', {}).get('name') or item.get('name')
                            if name:
                                names.append(name)
                    print(f"  {sorted(names)}")
    except Exception as e:
        import traceback
        print(f"Error: {e}")
        traceback.print_exc()

asyncio.run(test_ns_extraction())
