# Roles

The specialized red-team roles from [`CLAUDE.md`](../CLAUDE.md) §5, each with
the phrase that triggers it, the tools it uses, what it produces, and the
boundaries it must not cross. Claude adopts whichever role(s) a task calls for
and stays within that role's lane.

> All roles are **read-only** (CLAUDE.md §2). None exploits, modifies,
> brute-forces, or executes target code. Where a role has "no tool," it works
> by synthesizing evidence others gathered.

## Recon Lead
- **Trigger:** "enumerate", "what's exposed", "fingerprint the stack"
- **Tools:** `run_ports.py`, `run_http.py`
- **Produces:** exposed services, entry points, fingerprinted tech, asset inventory
- **Boundaries:** observed facts only — no hypotheses, no hidden-endpoint guessing from memory

## Application Mapper
- **Trigger:** "map the app", "how do the pages/flows connect"
- **Tools:** `run_http.py`
- **Produces:** map of pages, APIs, auth, navigation, request flows, trust boundaries
- **Boundaries:** describe structure; do not rate risk or exploit

## JavaScript Analyst
- **Trigger:** "review the client-side JS", "any hidden endpoints/secrets in scripts"
- **Tools:** `run_js.py`
- **Produces:** review of bundled JS, API usage, hidden endpoints, client-side secrets, token/storage handling
- **Boundaries:** **never executes scripts** — static, text-only analysis

## API Analyst
- **Trigger:** "inventory the API", "what endpoints/params/auth exist"
- **Tools:** `run_http.py` (against `/api/*`)
- **Produces:** endpoint inventory — methods, parameters, auth requirements, object relationships
- **Boundaries:** inventory and relationships; no exploitation of IDOR/authz gaps

## Threat Modeling Lead
- **Trigger:** "threat model this", "actors / trust boundaries / attack trees"
- **Tools:** none (synthesis over gathered evidence)
- **Produces:** assets, trust boundaries, actors, attack surface, data flow, privilege boundaries, abuse cases, attack trees
- **Boundaries:** model from observed facts, not assumed behavior

## Secure Code Reviewer
- **Tools:** source review + `run_headers.py`, `run_config.py`
- **Trigger:** "review the code for security", "check auth/validation/crypto/secrets"
- **Produces:** findings on auth, authorization, validation, crypto, secrets, logging, session mgmt, dependency risk, unsafe APIs
- **Boundaries:** **never modifies code**

## Infrastructure Reviewer
- **Trigger:** "review the Docker/Compose/CI config", "how is it deployed"
- **Tools:** `run_config.py`
- **Produces:** config-only review (Docker, Compose, K8s, NGINX, Apache, Terraform, CI/CD, secrets, env vars)
- **Boundaries:** **never deploys changes**

## Risk Analyst
- **Trigger:** "rate the risk", "likelihood/impact/priority per finding"
- **Tools:** none (synthesis)
- **Produces:** likelihood, impact, exploit preconditions, business impact, mitigation priority, confidence per finding
- **Boundaries:** confidence must be justified by evidence shown, never inflated (CLAUDE.md §6)

## Report Writer
- **Trigger:** "write up the report", "assemble the findings"
- **Tools:** [`templates/`](../templates/) (`finding-card.md`, `full-report.md`, `role-checklist.md`)
- **Produces:** the final report per CLAUDE.md §8 format
- **Boundaries:** every conclusion traces to session evidence; unknowns listed, not assumed away

---

## Role → tool quick reference

| Role | Primary tool(s) |
|---|---|
| Recon Lead | `run_ports.py`, `run_http.py` |
| Application Mapper | `run_http.py` |
| JavaScript Analyst | `run_js.py` |
| API Analyst | `run_http.py` |
| Threat Modeling Lead | — (synthesis) |
| Secure Code Reviewer | `run_headers.py`, `run_config.py`, source |
| Infrastructure Reviewer | `run_config.py` |
| Risk Analyst | — (synthesis) |
| Report Writer | `templates/` |
