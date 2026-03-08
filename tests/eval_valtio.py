"""Scanner evaluation script for Valtio support.

Scans Valtio sample files and outputs detected artifacts for manual comparison.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from codetrellis.valtio_parser_enhanced import EnhancedValtioParser


def main() -> None:
    """Run scanner evaluation on Valtio sample files."""
    parser = EnhancedValtioParser()

    sample_dir = os.path.join(os.path.dirname(__file__), 'eval', 'valtio_sample')
    files = sorted(f for f in os.listdir(sample_dir) if f.endswith(('.ts', '.tsx', '.js', '.jsx')))

    for fname in files:
        fpath = os.path.join(sample_dir, fname)
        with open(fpath, 'r') as f:
            content = f.read()

        print(f"\n{'='*70}")
        print(f"FILE: {fname}")
        print(f"{'='*70}")

        # Check detection
        is_valtio = parser.is_valtio_file(content)
        print(f"  is_valtio_file: {is_valtio}")

        if not is_valtio:
            continue

        r = parser.parse(content, fpath)

        # Proxies
        print(f"\n  PROXIES ({len(r.proxies)}):")
        for p in r.proxies:
            print(f"    - {p.name} (line {p.line_number}, exported={p.is_exported}, ts_type={p.type_name})")
            if p.state_fields:
                print(f"      fields: {p.state_fields}")
            if p.computed_getters:
                print(f"      getters: {p.computed_getters}")
            if p.has_ref:
                print(f"      has_ref: True")
            if p.has_nested_proxy:
                print(f"      has_nested_proxy: True")

        # Refs
        print(f"\n  REFS ({len(r.refs)}):")
        for rf in r.refs:
            print(f"    - {rf.name} (line {rf.line_number}, target={rf.ref_target})")

        # Collections
        print(f"\n  COLLECTIONS ({len(r.collections)}):")
        for c in r.collections:
            print(f"    - {c.name} ({c.collection_type}, line {c.line_number})")

        # Snapshots
        print(f"\n  SNAPSHOTS ({len(r.snapshots)}):")
        for s in r.snapshots:
            print(f"    - {s.name} ({s.snapshot_type}, proxy={s.proxy_name}, line {s.line_number})")
            if s.destructured_fields:
                print(f"      destructured: {s.destructured_fields}")
            if s.has_sync_option:
                print(f"      sync: True")

        # Use Proxies
        print(f"\n  USE_PROXIES ({len(r.use_proxies)}):")
        for up in r.use_proxies:
            print(f"    - {up.name} (proxy={up.proxy_name}, line {up.line_number})")

        # Subscriptions
        print(f"\n  SUBSCRIBES ({len(r.subscribes)}):")
        for s in r.subscribes:
            print(f"    - proxy={s.proxy_name}, unsub={s.unsubscribe_name} (line {s.line_number})")

        # Subscribe Keys
        print(f"\n  SUBSCRIBE_KEYS ({len(r.subscribe_keys)}):")
        for sk in r.subscribe_keys:
            print(f"    - proxy={sk.proxy_name}, key={sk.key_name} (line {sk.line_number})")

        # Watches
        print(f"\n  WATCHES ({len(r.watches)}):")
        for w in r.watches:
            print(f"    - tracked={w.tracked_proxies} (line {w.line_number})")

        # Actions
        print(f"\n  ACTIONS ({len(r.actions)}):")
        for a in r.actions:
            print(f"    - {a.name} (line {a.line_number}, async={a.is_async}, exported={a.is_exported})")

        # Devtools
        print(f"\n  DEVTOOLS ({len(r.devtools_configs)}):")
        for d in r.devtools_configs:
            print(f"    - proxy={d.proxy_name}, label={d.label} (line {d.line_number})")

        # Imports
        print(f"\n  IMPORTS ({len(r.imports)}):")
        for i in r.imports:
            print(f"    - from '{i.source}': {i.imported_names} (line {i.line_number})")

        # Types
        print(f"\n  TYPES ({len(r.types)}):")
        for t in r.types:
            print(f"    - {t.type_name} (context={t.context}, line {t.line_number})")

        # Integrations
        print(f"\n  INTEGRATIONS ({len(r.integrations)}):")
        for ig in r.integrations:
            print(f"    - {ig.integration}: {ig.imported_names} (line {ig.line_number})")

        # Framework/Feature Detection
        print(f"\n  FRAMEWORKS: {r.detected_frameworks}")
        print(f"  FEATURES: {r.detected_features}")
        print(f"  VERSION: {r.valtio_version}")


if __name__ == '__main__':
    main()
