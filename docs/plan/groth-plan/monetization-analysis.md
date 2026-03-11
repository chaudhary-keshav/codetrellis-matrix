# CodeTrellis Monetization Analysis

> Internal strategy document — March 2026
> Honest assessment for solo developer decision-making

---

## 1. Honest Assessment

You've built impressive technology. Income is possible but not imminent.

**What's real:**

- 120+ language/framework parsers with deep semantic extraction
- 6,985 passing tests across a comprehensive test suite
- Sophisticated architecture: JIT context, MCP server, distributed generation, cache optimization
- A working product that solves a genuine problem (AI context injection for large codebases)

**What's missing:**

- 0 GitHub stars
- 0 external users
- 0 PyPI presence (not published)
- 7 commits, 1 contributor
- Version number chaos: `4.16.0` in cache paths, `5.1.0` and `5.4.0` referenced elsewhere
- No blog posts, no conference talks, no community presence

**The gap:** You have a product. You do not yet have a project. Products generate revenue when people use them. Right now, nobody outside this repo knows CodeTrellis exists.

---

## 2. What Needs to Happen Before Any Money (Phase 0)

None of the revenue models below work without these prerequisites. This is the work that matters most right now.

### Must-Do (Month 0–3)

- [ ] **Fix version numbers** — Pick one version (e.g., `1.0.0` or `5.0.0`), sync it across `pyproject.toml`, cache paths, CLI output, and all references. Version chaos disqualifies you from enterprise evaluation instantly.
- [ ] **Publish to PyPI** — `pip install codetrellis` must work. This is table stakes. Without it, you don't exist in the Python ecosystem.
- [ ] **Make the repo public** — Clean up commit history if needed, ensure README is polished, add screenshots/GIFs of the tool in action.
- [ ] **Write a clear README** — Problem → Solution → Install → Quick Start → How It Works. Under 3 minutes to understand.
- [ ] **Set up GitHub Sponsors** — Takes 30 minutes. Even with 0 sponsors, having the button signals legitimacy.

### Should-Do (Month 3–6)

- [ ] **Write 3–5 blog posts / tutorials:**
  - "How CodeTrellis improves GitHub Copilot output by 40%"
  - "Building a universal code parser in Python: lessons from 120+ languages"
  - "Why AI coding assistants need project context (and how to give it to them)"
  - "MCP servers explained: giving Claude/Copilot your entire codebase"
  - A technical deep-dive on one novel piece of the architecture
- [ ] **Present at 1–2 meetups** — Local Python meetups, virtual AI/dev-tools meetups. A 15-minute lightning talk is enough.
- [ ] **Share strategically** — r/programming, Hacker News, dev.to, Python Discord, relevant Slack communities. Not spam; genuine "I built this" posts with substance.
- [ ] **Engage with the MCP ecosystem** — Anthropic's MCP community, VS Code extension marketplace discussions, related GitHub issues.

### Target Metrics at 6 Months

| Metric                 | Target       | Why It Matters                           |
| ---------------------- | ------------ | ---------------------------------------- |
| GitHub stars           | 100+         | Social proof for sponsors and enterprise |
| PyPI downloads/week    | 500+         | Proves real usage, not just curiosity    |
| Blog post views        | 5,000+ total | Funnel for awareness                     |
| Contributors           | 3–5          | Shows the project isn't bus-factor-1     |
| Open issues from users | 10+          | Proves people are trying to use it       |

If you haven't hit these numbers by month 6, the revenue projections below shift further right. That's fine — adjust, don't abandon.

---

## 3. Revenue Models Ranked by Realism

Ordered from most to least realistic for a solo developer starting from zero community.

### Tier 1: GitHub Sponsors / Open Collective

**Expected revenue:** $0–500/month
**Prerequisites:** 500+ stars, active community, regular releases
**Timeline:** Month 6–12 (earliest realistic first dollar)

| Comparable Tool                                           | Stars | Sponsors Revenue (est.)       |
| --------------------------------------------------------- | ----- | ----------------------------- |
| [Ruff](https://github.com/astral-sh/ruff)                 | 35K+  | Raised VC, not sponsor-funded |
| [tree-sitter](https://github.com/tree-sitter/tree-sitter) | 18K+  | ~$2K/mo via sponsors          |
| [pre-commit](https://github.com/pre-commit/pre-commit)    | 13K+  | Modest sponsor income         |
| [PyRight](https://github.com/microsoft/pyright)           | 13K+  | Microsoft-backed              |

**Reality:** Sponsor income alone rarely exceeds $1K/month for developer tools unless you have 5K+ stars and a devoted community. This is supplemental income, not a business model. But it's the easiest to set up and costs nothing.

### Tier 2: Consulting / Onboarding Packages

**Expected revenue:** $5K–30K/year
**Prerequisites:** 2–3 clients who already use the tool, published case studies
**Timeline:** Month 12–24

**What you'd sell:**

- CodeTrellis setup and customization for a team's monorepo ($2K–5K one-time)
- Custom parser development for niche frameworks ($3K–10K per parser)
- AI workflow optimization consulting ($75–150/hr starting, $150–300/hr once established)

**Honest rate guidance:** Start at $75–150/hr. You're a solo developer with no public consulting track record. The $150–300/hr range is achievable after 2–3 successful engagements and testimonials. Charging enterprise rates without enterprise references doesn't work.

| Comparable Solo Consultant Model | Rate Range                             | How They Got There                     |
| -------------------------------- | -------------------------------------- | -------------------------------------- |
| Independent DevOps consultants   | $100–250/hr                            | 2–3 years of content + OSS credibility |
| Tailwind CSS (Adam Wathan)       | Started consulting, pivoted to product | Years of blog/podcast audience first   |
| Caleb Porzio (Livewire)          | Sponsors + consulting                  | Built audience via screencasts         |

**Reality:** Consulting scales linearly with your time. It's good bridge income but caps out. The first client is the hardest — you'll likely need to offer a deeply discounted or free engagement to build the case study.

### Tier 3: Open-Core Enterprise License

**Expected revenue:** $10K–80K/year
**Prerequisites:** 1,000+ stars, 5+ enterprise evaluation requests, working enterprise features
**Timeline:** Month 24–36

**What you'd sell:**

- Multi-repo matrix graph ($500–2K/month per team)
- Team matrix server with shared context ($200–1K/month)
- SSO integration and audit logging ($500–1.5K/month)
- Priority support SLA ($500–2K/month)

| Comparable Open-Core Tool                 | Free Tier         | Paid Tier                          | Annual Revenue         |
| ----------------------------------------- | ----------------- | ---------------------------------- | ---------------------- |
| [SonarQube](https://www.sonarsource.com/) | Community Edition | Developer+ ($150+/yr)              | $200M+ (large company) |
| [GitLens](https://www.gitkraken.com/)     | Free VS Code ext  | Pro ($12/mo)                       | Acquired by GitKraken  |
| [Pulumi](https://www.pulumi.com/)         | CLI + SDK free    | Team ($50/mo/user)                 | Raised $100M+ VC       |
| [Nx](https://nx.dev/)                     | CLI free          | Nx Cloud (from free to enterprise) | VC-funded              |

**Reality:** These companies all had thousands of users before charging. SonarQube was free for years before enterprise tiers. You need proven demand before building enterprise features. Don't build SSO for zero users.

### Tier 4: Hosted Team Platform

**Expected revenue:** $50K+/year
**Prerequisites:** Proven demand from Tier 3, infrastructure investment, possibly funding
**Timeline:** Month 36+

This is the long-term play: a hosted CodeTrellis service that teams use without self-hosting. Think "Vercel for code context." This is only worth pursuing if Tier 3 proves there's willingness to pay.

**Reality:** Don't think about this yet. It requires infrastructure, support, security certifications, and significant capital. File it away and revisit if you reach 2,000+ stars and paying customers.

---

## 4. Licensing Strategy

### Recommended Approach

| Component                                                                | License     | Rationale                                                          |
| ------------------------------------------------------------------------ | ----------- | ------------------------------------------------------------------ |
| Core (all parsers, CLI, single-user MCP, JIT context, compressor, cache) | **MIT**     | Maximum adoption, no friction, community growth                    |
| NEW enterprise modules (multi-repo graph, team server, SSO, audit logs)  | **BSL 1.1** | Protects commercial value, converts to open-source after 3–4 years |

### Important Notes

- **MIT cannot be retroactively changed.** Everything currently in the repo stays MIT forever. Only new code in new modules can be BSL.
- **BSL (Business Source License)** allows free use for non-production and evaluation. Production use above a usage threshold requires a commercial license. After a defined period (typically 3–4 years), BSL code converts to a permissive license.
- **BSL community perception risk is real.** HashiCorp's Terraform BSL switch caused significant backlash and a fork (OpenTofu). However, that involved _changing_ an existing license. Starting new modules as BSL from day one is more accepted.
- **Precedents:** MariaDB (BSL originator), CockroachDB, Sentry, HashiCorp all use BSL variants. For a small project, this is less controversial — nobody forks a 0-star project.

### When to Implement BSL

Not now. Implement BSL only when:

1. You actually have enterprise features to protect
2. You have users who might pay for them
3. The core MIT project has enough traction that the BSL modules add clear incremental value

---

## 5. Enterprise Feature Boundary

### Free (MIT) — Everything a Solo Developer Needs

- All 120+ language/framework parsers
- CLI (`scan`, `prompt`, `watch`, `context`, etc.)
- Single-user MCP server
- JIT context engine
- Cache optimization
- Distributed file generation
- All best practices detection
- Skills generation
- Full matrix export

### Paid (BSL) — Team/Multi-Developer Features

Build these only when users ask for them:

- **Multi-repo matrix graph** — Link matrices across repositories, resolve cross-repo type references
- **Team matrix server** — Shared, persistent MCP server for teams with role-based access
- **SSO integration** — SAML/OIDC for enterprise identity management
- **Audit logging** — Track who queried what context, compliance reporting
- **SLA support** — Guaranteed response times, dedicated Slack channel
- **Usage analytics dashboard** — Which parsers get used, context hit rates

### Pattern Match

This boundary mirrors successful open-core tools:

| Tool      | Free                             | Paid                                              |
| --------- | -------------------------------- | ------------------------------------------------- |
| Docker    | Docker Engine, CLI               | Docker Desktop (business), Docker Scout           |
| Pulumi    | CLI, SDKs, all providers         | Team features, audit logs, SSO                    |
| SonarQube | Community Edition (17 languages) | Developer+ (more languages, branch analysis)      |
| GitLab    | Core CI/CD, repos                | SAML, audit events, compliance, security scanning |

The principle: **"individual developer productivity is free, team coordination is paid."**

---

## 6. Realistic Timeline

| Phase                | Timeline    | Revenue         | Prerequisites                                                          | Key Metric                            |
| -------------------- | ----------- | --------------- | ---------------------------------------------------------------------- | ------------------------------------- |
| **0: Foundation**    | Month 0–6   | **$0**          | Fix versions, publish PyPI, go public, write content, build community  | 100+ stars                            |
| **1: Traction**      | Month 6–12  | **$0–2K**       | GitHub Sponsors live, first blog readers, early adopters filing issues | 500+ stars, 500+ downloads/week       |
| **2: First Revenue** | Month 12–24 | **$2K–15K/yr**  | First consulting clients, growing community, conference talks          | 1,000+ stars, 2–3 paying clients      |
| **3: Sustainable**   | Month 24–36 | **$15K–80K/yr** | Enterprise features built, first enterprise customers, team licenses   | 2,000+ stars, 5+ enterprise customers |

### Probability-Weighted Scenarios

| Scenario                                   | Probability | Year 1 Income | Year 2 Income |
| ------------------------------------------ | ----------- | ------------- | ------------- |
| **Project doesn't gain traction**          | 50%         | $0            | $0            |
| **Modest community, sponsors only**        | 30%         | $0–500        | $1K–5K        |
| **Strong traction, consulting + sponsors** | 15%         | $1K–3K        | $5K–20K       |
| **Breakout success, enterprise demand**    | 5%          | $2K–5K        | $20K–80K      |

The median outcome is $0–500 in year 1. Plan accordingly.

---

## 7. The Hard Truth

**Most open-source developer tools never generate meaningful income.** The ones that do share these traits:

1. **Years of sustained community building** — Ruff, tree-sitter, Prettier, ESLint all took 2–4 years before any commercial model existed
2. **A large, active user base first** — Revenue follows adoption, never the reverse
3. **Marketing and visibility matter more than features** — A mediocre tool with great marketing beats an excellent tool nobody knows about
4. **Technical excellence is necessary but not sufficient** — You have the technical part. The marketing/community part is where most solo devs fail because it's uncomfortable and unfamiliar.

### The Competitive Window

ct-research estimated 2–3 years before AI vendors build perfect context engines. ct-verify challenged this as 12–18 months. The honest answer: **it depends on what "perfect" means.**

- GitHub Copilot, Cursor, and Windsurf are improving their built-in context rapidly
- But they optimize for the common case, not for deep multi-language semantic extraction
- CodeTrellis's niche — framework-aware parsing across 120+ parsers — is unlikely to be replicated by AI vendors in 18 months
- The real risk isn't feature parity but "good enough" — if built-in context gets 80% as good, the market for deep context tools shrinks

**Action implication:** Don't spend 2 years building in stealth. The window for establishing CodeTrellis as the name in deep code context is now. Ship, share, and build community while the gap is widest.

### The Fallback Value

Even if CodeTrellis never generates a dollar of revenue:

- It demonstrates deep engineering skill across 120+ languages/frameworks
- The parser architecture is a portfolio piece that stands out in any senior/staff engineering interview
- The MCP server integration positions you at the frontier of AI-assisted development
- The knowledge you've built about code analysis, AST parsing, and AI context is genuinely rare
- You can pivot this expertise into a well-paying role at any AI coding tool company

**This is not wasted work regardless of monetization outcomes.**

---

## 8. Recommendation: What to Do This Week

In priority order — each takes less than a day:

1. **Fix version numbers.** Search for `4.16.0`, `5.1.0`, `5.4.0` across the codebase. Pick one canonical version. Update everywhere. This is a 2-hour task that removes a red flag.

2. **Publish to PyPI.** Run `python -m build && twine upload dist/*`. Ensure `pip install codetrellis` works cleanly. This is the single highest-leverage action.

3. **Set up GitHub Sponsors.** Go to github.com/sponsors, fill out the profile. Even with zero income, it signals "this project accepts support."

4. **Write one blog post.** Start with "How CodeTrellis gives GitHub Copilot full project context via MCP." Post it on dev.to and share the link.

5. **Share in communities.** Post a genuine "Show HN" or "Show r/programming" once the PyPI package is live and README is polished. One good launch post matters more than 10 mediocre ones.

6. **Don't build enterprise features yet.** Every hour spent on SSO or multi-repo right now is an hour not spent on the community building that makes SSO worth building later.

---

## Summary

| Question                            | Answer                                                            |
| ----------------------------------- | ----------------------------------------------------------------- |
| Is the technology real?             | Yes — 120+ parsers, 6,985 tests, genuine innovation               |
| Can it generate income?             | Yes — but not yet, and not without community first                |
| How much in year 1?                 | Honestly: $0–2K (median: $0–500)                                  |
| What's the highest-leverage action? | Publish to PyPI and write one blog post                           |
| What should you NOT do?             | Build enterprise features or optimize pricing before having users |
| What's the long-term potential?     | $15K–80K/yr is achievable in 2–3 years with sustained effort      |
| What if it never monetizes?         | It's still a standout portfolio piece and deep domain expertise   |

---

_This document should be revisited at month 3 and month 6 to check progress against Phase 0 metrics._
