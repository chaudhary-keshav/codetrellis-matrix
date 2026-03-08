#!/usr/bin/env python3
"""
PoC: Cross-Language Type Mapping (F5)
========================================
Tests polyglot type resolution across 19 languages.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))


def main():
    print("=" * 60)
    print("F5 PoC: Cross-Language Type Mapping")
    print("=" * 60)

    from codetrellis.cross_language_types import CrossLanguageLinker

    linker = CrossLanguageLinker()
    langs = linker.get_available_languages()
    print(f"Available languages: {len(langs)}")
    print(f"Languages: {', '.join(sorted(langs))}")

    # Test primitive mappings
    test_cases = [
        ("python", "str", "typescript"),
        ("python", "int", "java"),
        ("rust", "Vec", "go"),
        ("kotlin", "Boolean", "csharp"),
        ("swift", "String", "ruby"),
        ("java", "CompletableFuture", "python"),
        ("python", "float", "rust"),
        ("typescript", "number", "python"),
        ("go", "string", "java"),
        ("csharp", "int", "python"),
        ("scala", "Int", "kotlin"),
        ("dart", "String", "swift"),
        ("php", "string", "python"),
        ("ruby", "Integer", "java"),
        ("lua", "string", "python"),
    ]

    print("\nType mappings:")
    passed = 0
    for src_lang, src_type, tgt_lang in test_cases:
        result = linker.resolve_type(src_type, src_lang, tgt_lang)
        status = "✅" if result else "❌"
        if result:
            passed += 1
        print(f"  {status} {src_lang}:{src_type} → {tgt_lang}:{result or 'UNMAPPED'}")

    print(f"\nPassed: {passed}/{len(test_cases)}")
    print("\n✅ F5 PoC PASSED" if passed == len(test_cases) else "\n⚠️ F5 PoC PARTIAL")
    return 0


if __name__ == "__main__":
    sys.exit(main())
