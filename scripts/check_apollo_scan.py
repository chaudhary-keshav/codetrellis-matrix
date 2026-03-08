"""Quick script to check Apollo scan results from JSON output."""
import json
import sys

def check_apollo_fields(json_path):
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    repo_name = json_path.split('/')[-2]
    print(f"\n=== Apollo Fields in {repo_name} ===")
    
    # Check the nested apollo section
    apollo = data.get('apollo', {})
    if apollo:
        for k, v in sorted(apollo.items()):
            if isinstance(v, list):
                print(f"  apollo.{k}: {len(v)} items")
            elif isinstance(v, str):
                print(f"  apollo.{k}: {v}")
            else:
                print(f"  apollo.{k}: {v}")
    else:
        print("  No 'apollo' section in JSON")
    
    # Check stats section
    stats = data.get('stats', {})
    apollo_stats = {k: v for k, v in stats.items() if 'apollo' in k.lower()}
    if apollo_stats:
        print(f"\n  Stats: {apollo_stats}")
    
    # Check TypeScript framework detection
    ts = data.get('typescript', {})
    ts_fw = ts.get('detected_frameworks', []) if isinstance(ts, dict) else []
    js = data.get('javascript', {})
    js_fw = js.get('detected_frameworks', []) if isinstance(js, dict) else []
    
    print(f"\n  TypeScript frameworks: {ts_fw}")
    print(f"  JavaScript frameworks: {js_fw}")
    print(f"  Apollo version (apollo section): {apollo.get('version', 'N/A')}")
    
    # Show [APOLLO_*] sections in the prompt
    prompt_path = json_path.replace('matrix.json', 'matrix.prompt')
    try:
        with open(prompt_path, 'r') as f:
            content = f.read()
        apollo_sections = [line for line in content.split('\n') if '[APOLLO' in line]
        if apollo_sections:
            print(f"\n  Prompt sections: {apollo_sections}")
    except FileNotFoundError:
        pass

if __name__ == '__main__':
    check_apollo_fields(sys.argv[1])
