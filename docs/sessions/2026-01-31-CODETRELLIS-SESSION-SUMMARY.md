# Session Summary: CodeTrellis - Project Self-Awareness System

**Date**: January 30-31, 2026
**Duration**: ~4-5 hours across 2 sessions
**Status**: ✅ MVP Complete

---

## 🎯 Objective

Create a system that gives AI **instant, deep understanding** of any project without reading every file. The goal was to compress entire codebases into minimal tokens that can be injected into AI prompts.

### The Problem We Solved

- AI (Claude/Copilot) was only reading 50-100 lines per file
- Every new session required AI to re-learn the project
- No persistent "project memory" between sessions
- Large projects = too many tokens = expensive/slow

### The Solution

**CodeTrellis (Project Self-Awareness System)** - Compresses project structure to ~2% of original size while preserving all essential information.

---

## 📁 What We Built

### File Structure Created

```
/tools.codetrellis/
├── README.md
├── requirements.txt
├── pyproject.toml
└──.codetrellis/
    ├── __init__.py
    ├── cli.py                    # CLI interface
    ├── scanner.py                # Project scanner
    ├── compressor.py             # Token compressor
    ├── distributed_generator.py  # Distributed .codetrellis files
    ├── watcher.py                # File watcher (for auto-sync)
    └── parsers/
        ├── __init__.py
        ├── typescript.py         # TypeScript/NestJS parser
        ├── python_parser.py      # Python parser
        ├── proto.py              # gRPC Proto parser
        └── angular.py            # Angular component parser
```

### Two Operating Modes

#### 1. Centralized Mode (`codetrellis scan`)

- Creates single `matrix.prompt` file
- Best for: NestJS backend projects
- Output: `.codetrellis/cache/1.0.0/{project}/matrix.prompt`

#### 2. Distributed Mode (.codetrellis distribute`) ⭐

- Creates `.codetrellis` file in EACH component folder
- Best for: Angular/React frontend projects
- AI reads local context on-demand

---

## 📊 Compression Results

### Trading-UI Project (Angular)

| Metric         | Before          | After          | Reduction |
| -------------- | --------------- | -------------- | --------- |
| Total Size     | 1,267,492 bytes | 23,759 bytes   | **98.1%** |
| Token Estimate | ~316,873 tokens | ~5,940 tokens  | **98.1%** |
| Files          | 200+ TS files   | 79 .codetrellis files | -         |

### NS-Brain Monorepo (Full Project)

| Metric        | Value                  |
| ------------- | ---------------------- |
| Files Scanned | 68,503                 |
| Schemas Found | 123                    |
| DTOs Found    | 119                    |
| Controllers   | 91                     |
| Components    | 55                     |
| gRPC Services | 24                     |
| Output Size   | ~57KB (~14,000 tokens) |

---

## 🔧 CLI Commands

```bash
# Navigate to CodeTrellis tool
cd /tools.codetrellis

# Scan entire project (centralized)
python3 -m.codetrellis.cli scan /path/to/project

# Generate distributed .codetrellis files
python3 -m.codetrellis.cli distribute /path/to/project

# Show compressed matrix
python3 -m.codetrellis.cli show /path/to/project

# Show only schemas
python3 -m.codetrellis.cli show /path/to/project --schemas

# Initialize CodeTrellis in a project
python3 -m.codetrellis.cli init /path/to/project
```

---

## 📝 Sample Output

### Distributed .codetrellis File (Component)

```
# PnLTrendChartComponent
type=component|standalone,OnPush,signals
inputs:data,title,showCumulative,daysToShow
signals:chartData,maxPnl,maxCumulative,totalPnl,avgPnl,winDays,loseDays
methods:getBarHeight,getBarStyle,getCumulativeY,getCumulativePath
interfaces:PnLDataPoint{date,pnl,pnlPercent,cumulativePnl}
```

### Centralized Matrix (Schema)

```
[SCHEMAS]
VixData|fields:value!,previousValue|ts
NiftyData|fields:value!,change!,changePercent!,gap,gapPercent,atr20|ts
MarketBreadthData|fields:advances!,declines!,unchanged,advanceDeclineRatio!|ts
```

---

## 🐛 Bugs Fixed

### 1. Schema Field Duplication Bug

**Problem**: Parser was extracting ALL `@Prop` fields from entire file instead of per-class
**Symptom**: Every schema had the same 50+ fields
**Fix**: Implemented brace-matching to extract class body FIRST, then parse fields within that body only

### 2. Optional Import Handling

**Problem**: `watchdog` package not installed caused import errors
**Fix**: Made imports graceful with try/except blocks

---

## 🚀 How It Works

### Workflow for AI

1. **Session Start**: AI reads main `.codetrellis-prompt` file (~850 tokens)
2. **Working on Component**: AI reads local `.codetrellis` file in that folder
3. **AI Knows**:
   - Component features (standalone, OnPush, signals)
   - Existing inputs/outputs
   - Available methods
   - Local interfaces
4. **AI Writes Correct Code**: Following existing patterns automatically

### Example

```
User: "Add currency symbol input to PnLTrendChartComponent"

AI reads: .codetrellis file
AI sees: inputs:data,title,showCumulative,daysToShow
AI writes: readonly currencySymbol = input<string>('₹');

AI automatically:
✅ Uses input() not @Input()
✅ Follows readonly pattern
✅ Provides default value
```

---

## 📋 TODO / Future Work

### High Priority

- [ ] Generate prompt template automatically (`codetrellis prompt-template`)
- [ ] VS Code extension for auto-injection
- [ ] Watch mode for auto-sync on file changes
- [ ] NestJS DTO validation decorator extraction

### Medium Priority

- [ ] React/Vue component parsers
- [ ] Python Django/FastAPI parsers
- [ ] Dependency graph visualization
- [ ] Token budget warnings

### Low Priority

- [ ] Cloud sync for team sharing
- [ ] AI model fine-tuning with CodeTrellis data
- [ ] Marketplace/monetization

---

## 💡 Key Insights

1. **Distributed > Centralized** for frontend projects
   - Components are self-contained
   - AI only needs local context

2. **98% Compression** is achievable
   - Most code is implementation details
   - Structure/signatures are what AI needs

3. **Brace Matching** is essential for TypeScript
   - Regex alone fails with nested structures
   - Must extract class body before parsing fields

4. **Token Budget Matters**
   - Main prompt: ~1000 tokens (rules + architecture)
   - Local context: ~200-500 tokens per component
   - Total per task: ~1500-2000 tokens

---

## 📍 Files Modified

### Created

- `/tools.codetrellis/` - Entire CodeTrellis tool
- `/ai/trading-ui/.codetrellis-prompt` - Main prompt template
- `/ai/trading-ui/src/app/**/.codetrellis` - 79 distributed files

### Modified

- `/.gitignore` - Added `.codetrellis` patterns
- `/ai/trading-ui/.gitignore` - Added `.codetrellis` patterns

---

## 🎉 Success Metrics

| Goal                             | Status                             |
| -------------------------------- | ---------------------------------- |
| Compress project to <2000 tokens | ✅ Main prompt ~850 tokens         |
| Preserve essential structure     | ✅ All schemas/components captured |
| Auto-detect stack versions       | ✅ NestJS 10, Angular 19 detected  |
| Per-component context            | ✅ Distributed .codetrellis files         |
| CLI interface                    | ✅ scan, distribute, show, init    |

---

## 📚 References

- Inspiration: Angular's `.angular/cache` structure
- Similar to: TypeScript's `tsconfig.json` project references
- Compression approach: Similar to AST summary extraction

---

**Next Session Goal**: Build the prompt generator that combines `.codetrellis-prompt` + user task into optimal AI prompt.
