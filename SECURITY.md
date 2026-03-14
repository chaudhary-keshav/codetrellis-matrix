# Security Policy

## Supported Versions

Only the latest release receives security updates.

| Version | Supported |
| ------- | --------- |
| 1.0.x   | ✅ Yes    |
| < 1.0   | ❌ No     |

## Reporting a Vulnerability

Please **do not** open a public GitHub issue for security vulnerabilities.

**How to report:**

1. **Email**: Send details to `security@nsbrain.ai`
2. **GitHub Security Advisory**: [Open a private advisory](https://github.com/chaudhary-keshav/codetrellis-matrix/security/advisories/new)

**Please include:**

- A clear description of the vulnerability
- Steps to reproduce
- Affected versions
- Potential impact

**Response SLA:**

- We will acknowledge receipt within **72 hours**
- We will provide an initial assessment within **7 days**
- We will coordinate a fix and disclosure timeline with you before making anything public

## Disclosure Policy

We follow coordinated (responsible) disclosure. Please give us reasonable time to address the issue before any public disclosure.

## Scope

CodeTrellis is a **static analysis tool** — it only reads source code files on the local filesystem. It does not:

- Execute user code
- Make outbound network requests (except optional MCP server connections)
- Transmit source code to external services
- Store credentials or secrets

Reports about low-severity issues (e.g., typos in docs, non-exploitable edge cases) may be handled via normal GitHub Issues instead.
