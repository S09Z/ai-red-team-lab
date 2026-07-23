# Assessment Workflow

How a full, evidence-driven assessment session runs against the lab. This
follows the governance in [`CLAUDE.md`](../CLAUDE.md): observation-first,
read-only, every conclusion traced to evidence gathered *this session*.

## The loop (never reorder)

```
Observe → Collect Evidence → Model → Hypothesize
   → Estimate Risk → Recommend Validation → Report
```

Evidence always precedes conclusions. Do not skip to "Findings" without
showing the Observe/Evidence steps that led there (CLAUDE.md §4).

## Before you start

1. **Confirm scope.** In-scope = the local target only (default
   `http://localhost:5000` and the source under `targets/flask-app/`). If
   scope is ambiguous, stop and ask (CLAUDE.md §1, §12).
2. **Confirm the target is healthy** — see [setup.md](setup.md).
3. **Open the checklist** — keep [`templates/role-checklist.md`](../templates/role-checklist.md)
   next to you; run it before finalizing anything.

## Session walkthrough

Each step is performed in a specific role (see [roles.md](roles.md)). Stay in
the role's lane and record evidence as you go.

### 1. Recon (Recon Lead)
Enumerate what is reachable. Fingerprint the tech.

```bash
python tools/run_ports.py --host localhost --ports 5000
python tools/run_http.py  --url http://localhost:5000/  --json
```

Capture: open ports, status codes, server/framework headers. → **Asset
Inventory**, **Technology Stack**.

### 2. Application & API mapping (Application Mapper / API Analyst)
Walk the observed entry points. For each page/endpoint, note method, auth
requirement, and parameters.

```bash
python tools/run_http.py --url http://localhost:5000/login
python tools/run_http.py --url http://localhost:5000/api/users --json
```

→ **Architecture Understanding**, **Attack Surface**, **Trust Boundaries**.

### 3. Client-side review (JavaScript Analyst)
Harvest and statically scan scripts — never execute them.

```bash
python tools/run_js.py --url http://localhost:5000/dashboard
```

→ hidden endpoints, client-side secrets, storage usage (candidates).

### 4. Header & config review (Secure Code Reviewer / Infrastructure Reviewer)
Audit security headers on live responses and scan config files on disk.

```bash
python tools/run_headers.py --url http://localhost:5000/
python tools/run_config.py  --file docker-compose.yml
python tools/run_config.py  --file targets/flask-app/config.py
```

→ missing headers, insecure cookies, secrets/debug/exposed ports.

### 5. Threat modeling (Threat Modeling Lead)
From the map and evidence, derive actors, trust boundaries, abuse cases, and
attack trees. No tool — this is synthesis over observed facts.

### 6. Risk rating (Risk Analyst)
For each hypothesis, assign likelihood, impact, preconditions, and a
**confidence** rating justified by the evidence shown (CLAUDE.md §6). Never
inflate certainty.

### 7. Validation planning
For every finding, recommend a **non-destructive** validation — config
review, source review, log review, manual verification, or a
unit/integration/regression test (CLAUDE.md §7). **Never validate by
exploiting.**

### 8. Report (Report Writer)
Assemble findings into [`templates/full-report.md`](../templates/full-report.md),
one [`finding-card.md`](../templates/finding-card.md) per issue. Each finding
carries all 8 evidence fields.

## Before submitting

Run every box in [`role-checklist.md`](../templates/role-checklist.md):
session-only evidence, all 8 fields, justified confidence, read-only,
loop-order followed, non-destructive validations, out-of-scope flagged,
unknowns listed, role reflected.

## Golden rules (CLAUDE.md §9)

Assume nothing · Observe everything · Justify every conclusion · Never
exploit · Never modify · Never damage · Always explain reasoning · When
uncertain, say "insufficient evidence."
