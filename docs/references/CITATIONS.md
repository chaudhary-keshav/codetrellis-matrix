# CodeTrellis Matrix — Research Sources & Citations

> **Document Type:** Formal Citation Registry  
> **Version:** 1.0.0  
> **Date:** 20 February 2026  
> **Author:** Keshav Chaudhary (CodeTrellis Creator)  
> **Reference:** CODETRELLIS_MASTER_RESEARCH_AND_PLAN.md — PART J, Section J4  
> **Status:** ✅ Complete

---

## Overview

This document formalizes all research sources, academic papers, industry tools, and standards referenced during the CodeTrellis Matrix strategic research session (February 2026). Each citation is linked to the specific CodeTrellis module or research topic it informs.

---

## 1. Standards & Specifications

### 1.1 JSON-LD 1.1 — W3C Recommendation

- **URL:** <https://www.w3.org/TR/json-ld11/>
- **Topic:** §F1 — JSON-LD / RDF for Semantic Matrix Sections
- **Module:** `codetrellis/matrix_jsonld.py`
- **Usage:** JSON-LD 1.1 context structure, `@graph` encoding, `@id` node identifiers for matrix sections. Enables semantic interoperability with RDF-aware tools and knowledge graphs.

### 1.2 schema.org/SoftwareSourceCode

- **URL:** <https://schema.org/SoftwareSourceCode>
- **Topic:** §F1 — JSON-LD / RDF for Semantic Matrix Sections
- **Module:** `codetrellis/matrix_jsonld.py`
- **Usage:** Schema.org vocabulary for `SoftwareSourceCode`, `CodeAction`, `ComputerLanguage` types. Provides standardized vocabulary for code entity descriptions in JSON-LD output.

### 1.3 RFC 6902 — JavaScript Object Notation (JSON) Patch

- **URL:** <https://www.rfc-editor.org/rfc/rfc6902>
- **Topic:** §F3 — Differential Matrix via JSON Patch
- **Module:** `codetrellis/matrix_diff.py`
- **Usage:** JSON Patch operations (add, remove, replace, move, copy, test) for incremental matrix updates. Enables watch-mode with sub-500ms patch generation instead of full rebuilds.

### 1.4 RFC 6901 — JavaScript Object Notation (JSON) Pointer

- **URL:** <https://www.rfc-editor.org/rfc/rfc6901>
- **Topic:** §F3 — Differential Matrix via JSON Patch
- **Module:** `codetrellis/matrix_diff.py`
- **Usage:** JSON Pointer syntax for addressing specific values within matrix JSON documents. Foundation for RFC 6902 path expressions.

### 1.5 SCIP Protocol — Sourcegraph Code Intelligence Protocol

- **URL:** <https://github.com/sourcegraph/scip>
- **Topic:** §F5 — Cross-Language Matrix Merging via SCIP/LSIF
- **Module:** `codetrellis/cross_language_types.py`
- **Usage:** SCIP index format for cross-language type resolution. Unified type graph construction across 53+ languages using symbol descriptors and occurrence information.

### 1.6 LSIF — Language Server Index Format

- **URL:** <https://microsoft.github.io/language-server-protocol/overviews/lsif/overview/>
- **Topic:** §F5 — Cross-Language Matrix Merging via SCIP/LSIF
- **Module:** `codetrellis/cross_language_types.py`
- **Usage:** LSIF graph format for pre-computed language intelligence. Informs the design of cross-language type mapping and API link resolution.

---

## 2. Academic Papers

### 2.1 CodeBERT: A Pre-Trained Model for Programming and Natural Languages

- **Authors:** Feng, Z., Guo, D., Tang, D., et al.
- **Year:** 2020
- **Venue:** arXiv:2002.08155
- **Topic:** §F2 — Matrix Embeddings for Semantic Retrieval
- **Module:** `codetrellis/matrix_embeddings.py`
- **Usage:** CodeBERT's bi-modal pre-training approach (NL-PL) informs the design of code-aware embedding strategies. While CodeTrellis uses TF-IDF for zero-dependency operation, CodeBERT-style embeddings are supported as an optional upgrade path.

### 2.2 UniXcoder: Unified Cross-Modal Pre-training for Code Representation

- **Authors:** Guo, D., Lu, S., Duan, N., et al.
- **Year:** 2022
- **Venue:** arXiv:2203.03850
- **Topic:** §F2 — Matrix Embeddings for Semantic Retrieval
- **Module:** `codetrellis/matrix_embeddings.py`
- **Usage:** UniXcoder's unified cross-modal representation informs potential embedding model upgrades. Multi-modal (code + comment + AST) representations align with CodeTrellis's structured section approach.

### 2.3 LLMLingua: Compressing Prompts for Accelerated Inference of Large Language Models

- **Authors:** Jiang, H., Wu, Q., Lin, C.Y., Yang, Y., Qiu, L.
- **Year:** 2023
- **Venue:** EMNLP 2023
- **Topic:** §F4 — Matrix Compression Levels (L1/L2/L3) via LLMLingua
- **Module:** `codetrellis/matrix_compressor_levels.py`
- **Usage:** LLMLingua's token-level compression approach informs L2/L3 compression levels. Budget-constrained prompt compression with perplexity-based token importance scoring.

### 2.4 LongLLMLingua: Accelerating and Enhancing LLMs in Long Context Scenarios via Prompt Compression

- **Authors:** Jiang, H., Wu, Q., et al.
- **Year:** 2024
- **Venue:** ACL 2024
- **Topic:** §F4 — Matrix Compression Levels (L1/L2/L3) via LLMLingua
- **Module:** `codetrellis/matrix_compressor_levels.py`
- **Usage:** Long-context compression strategies for large matrix files. Question-aware compression preserves query-relevant sections.

### 2.5 LLMLingua-2: Data Distillation for Efficient and Faithful Task-Agnostic Prompt Compression

- **Authors:** Pan, Z., Wu, Q., et al.
- **Year:** 2024
- **Venue:** ACL 2024
- **Topic:** §F4 — Matrix Compression Levels (L1/L2/L3) via LLMLingua
- **Module:** `codetrellis/matrix_compressor_levels.py`
- **Usage:** Task-agnostic compression using data distillation. Informs the design of compression levels that work across different AI model targets.

### 2.6 SWE-bench: Can Language Models Resolve Real-World GitHub Issues?

- **Authors:** Jimenez, C.E., Yang, J., Wettig, A., et al.
- **Year:** 2024
- **Venue:** ICLR 2024 (Oral)
- **Topic:** §F7 — CodeTrellis Benchmark Suite (MatrixBench)
- **Module:** `codetrellis/matrixbench_scorer.py`
- **Usage:** SWE-bench's task structure (issue → patch → verification) informs MatrixBench's benchmark categories. Provides baseline comparison data for context-aware vs. context-free code generation.

### 2.7 SWE-bench Multimodal: Do AI Systems Generalize to Visual Software Domains?

- **Authors:** Yang, J., et al.
- **Year:** 2025
- **Venue:** ICLR 2025
- **Topic:** §F7 — CodeTrellis Benchmark Suite (MatrixBench)
- **Module:** `codetrellis/matrixbench_scorer.py`
- **Usage:** Multimodal extension considerations for future MatrixBench versions supporting visual context.

### 2.8 HumanEval: Evaluating Large Language Models Trained on Code

- **Authors:** Chen, M., Tworek, J., Jun, H., et al.
- **Year:** 2021
- **Venue:** arXiv:2107.03374
- **Topic:** §F7 — CodeTrellis Benchmark Suite (MatrixBench)
- **Module:** `codetrellis/matrixbench_scorer.py`
- **Usage:** HumanEval's function completion benchmark format informs MatrixBench's code generation accuracy measurement. Provides standardized metrics for comparing context-enhanced code completion.

### 2.9 DevBench: A Comprehensive Benchmark for Software Development

- **Authors:** Li, B., et al.
- **Year:** 2024
- **Venue:** arXiv:2403.08604
- **Topic:** §F7 — CodeTrellis Benchmark Suite (MatrixBench)
- **Module:** `codetrellis/matrixbench_scorer.py`
- **Usage:** DevBench's multi-task benchmark structure informs MatrixBench's category design (completeness, accuracy, compression, retrieval, consistency).

---

## 3. Industry Tools & Implementations

### 3.1 PyLD — JSON-LD Processor for Python

- **URL:** <https://github.com/digitalbazaar/pyld>
- **Topic:** §F1 — JSON-LD / RDF for Semantic Matrix Sections
- **Module:** `codetrellis/matrix_jsonld.py`
- **Usage:** Reference implementation for JSON-LD processing. CodeTrellis implements a lightweight JSON-LD encoder without the full PyLD dependency for zero-dependency operation.

### 3.2 python-json-patch — JSON Patch for Python

- **URL:** <https://github.com/stefankoegl/python-json-patch>
- **Topic:** §F3 — Differential Matrix via JSON Patch
- **Module:** `codetrellis/matrix_diff.py`
- **Usage:** Production dependency (`jsonpatch` package) for RFC 6902 JSON Patch generation and application. Used for incremental matrix updates and watch-mode differential builds.

### 3.3 LLMLingua — Prompt Compression Library

- **URL:** <https://github.com/microsoft/LLMLingua>
- **Topic:** §F4 — Matrix Compression Levels (L1/L2/L3) via LLMLingua
- **Module:** `codetrellis/matrix_compressor_levels.py`
- **Usage:** Reference for compression algorithm design. CodeTrellis implements AST-aware compression inspired by LLMLingua's token-level approach but specialized for structured code matrices.

### 3.4 MTEB Benchmark — Massive Text Embedding Benchmark

- **URL:** <https://huggingface.co/blog/mteb>
- **Topic:** §F2 — Matrix Embeddings for Semantic Retrieval
- **Module:** `codetrellis/matrix_embeddings.py`
- **Usage:** MTEB's evaluation framework informs embedding quality assessment. Provides baseline comparison for TF-IDF vs. neural embedding retrieval accuracy.

### 3.5 sentence-transformers — Sentence Embeddings

- **URL:** <https://www.sbert.net/>
- **Topic:** §F2 — Matrix Embeddings for Semantic Retrieval
- **Module:** `codetrellis/matrix_embeddings.py`
- **Usage:** SBERT's sentence embedding architecture informs optional neural embedding upgrade path. Compatible with CodeTrellis's section-level embedding granularity.

### 3.6 Sourcegraph Cody — AI Code Assistant

- **URL:** <https://sourcegraph.com/docs/cody/core-concepts/context>
- **Topic:** §F6 — Matrix-Guided File Discovery & Directed Retrieval
- **Module:** `codetrellis/matrix_navigator.py`
- **Usage:** Cody's context retrieval strategies (keyword, graph, embedding) inform MatrixNavigator's hybrid ranking approach combining structural and semantic signals.

### 3.7 SWE-bench — Software Engineering Benchmark

- **URL:** <https://www.swebench.com/>
- **Topic:** §F7 — CodeTrellis Benchmark Suite (MatrixBench)
- **Module:** `codetrellis/matrixbench_scorer.py`
- **Usage:** SWE-bench leaderboard data provides competitive baseline for CodeTrellis context effectiveness measurement.

### 3.8 Aider Polyglot — Multi-Language AI Coding

- **URL:** <https://aider.chat/2024/12/21/polyglot.html>
- **Topic:** §F7 — CodeTrellis Benchmark Suite (MatrixBench)
- **Module:** `codetrellis/matrixbench_scorer.py`
- **Usage:** Aider's polyglot benchmark approach informs MatrixBench's multi-language testing strategy across 53+ supported languages.

---

## 4. Competitive Intelligence Sources

### 4.1 Claude Code Documentation

- **URL:** <https://code.claude.com/docs>
- **Topic:** §A1.1 — Claude Code Memory Hierarchy
- **Usage:** Analysis of Claude Code's 7-layer memory system (managed policy → auto memory → skills → subagents) for competitive positioning. Identified weakness: zero structural knowledge at session start.

### 4.2 Gemini CLI

- **URL:** <https://github.com/google-gemini/gemini-cli>
- **Topic:** §A1.2 — Gemini CLI Context Strategy
- **Usage:** Analysis of GEMINI.md file-based context and 1M token window. Identified weakness: no pre-computed project map despite large context window.

### 4.3 Aider Repository Map

- **URL:** <https://aider.chat/docs/repomap.html>
- **Topic:** §A1.3 — Aider Repo Map (Closest Competitor)
- **Usage:** Analysis of tree-sitter AST parsing + graph ranking approach. Identified as closest competitor but limited to 1K token signatures-only map vs. CodeTrellis's 94K full knowledge graph.

### 4.4 Cursor Features

- **URL:** <https://cursor.com/features>
- **Topic:** §A1.4 — Cursor Embedding-Based Semantic Search
- **Usage:** Analysis of embedding-based `@codebase` queries and `.cursor/rules/*.md`. Identified weakness: textual similarity without structural relationships.

### 4.5 Cline

- **URL:** <https://github.com/cline/cline>
- **Topic:** §A1.5 — Cline AST + Tool Use
- **Usage:** Analysis of `.clinerules/`, skills, Memory Bank approach. Identified weakness: 10-30 tool calls for discovery per task in 484-file projects.

---

## 5. SWE-bench Leaderboard Reference (February 2026)

These results represent bash-only (no agent framework) SWE-bench scores used for competitive benchmarking in MatrixBench:

| Rank | Model           | Score | Cost/Instance |
| ---- | --------------- | ----- | ------------- |
| 1    | Claude 4.5 Opus | 76.8% | $0.75         |
| 2    | Gemini 3 Flash  | 75.8% | $0.36         |
| 3    | MiniMax M2.5    | 75.8% | $0.07         |
| 4    | Claude Opus 4.6 | 75.6% | $0.55         |
| 5    | GPT-5-2         | 72.8% | $0.47         |

---

## Citation Format

When referencing CodeTrellis research in publications or documentation, use:

```
Chaudhary, K. (2026). CodeTrellis Matrix — Master Research, Strategy & Implementation Plan.
Version 1.0.0. CodeTrellis Project. https://github.com/keshav4u/CodeTrellis
```

---

## Document History

| Version | Date             | Changes                                           |
| ------- | ---------------- | ------------------------------------------------- |
| 1.0.0   | 20 February 2026 | Initial citation registry from PART J, Section J4 |

---

_This citation registry is maintained as part of the CodeTrellis Matrix strategic research documentation._  
_Author: Keshav Chaudhary | CodeTrellis Creator_
