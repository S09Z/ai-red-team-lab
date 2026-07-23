<!--
Self-Verification Checklist — implements CLAUDE.md §10 (Analysis Requirements
Checklist). Run this BEFORE producing or finalizing any finding or report
section. Every box must be checked (or explicitly explained) before output.
-->

# Pre-Report Self-Verification Checklist

Confirm each item before finalizing any finding or report section:

- [ ] **Session-only evidence** — Have I used only facts observed in *this*
      session, with no memory of similar apps/CTFs? (CLAUDE.md §3)
- [ ] **All 8 evidence fields** — Does every finding include Observation,
      Evidence, Reasoning, Confidence, Possible Impact, Suggested Validation,
      Recommended Fix, and Unknowns? (CLAUDE.md §6)
- [ ] **Justified confidence** — Is each confidence rating supported by the
      evidence shown, not inflated? (CLAUDE.md §6)
- [ ] **Read-only** — Did I stay read-only: no file/db writes, no
      exploitation, no network egress beyond the defined scope? (CLAUDE.md §2)
- [ ] **Loop order** — Did I follow Observe → Evidence → Model → Hypothesize
      → Risk → Validation → Report without skipping steps? (CLAUDE.md §4)
- [ ] **Non-destructive validation** — Are all recommended validations
      non-destructive? (CLAUDE.md §7)
- [ ] **Out-of-scope flagged** — Did I flag anything out-of-scope instead of
      investigating it? (CLAUDE.md §1, §12)
- [ ] **Unknowns listed** — Did I list open/unknown items rather than
      silently assuming they are fine? (CLAUDE.md §6, §8.11)
- [ ] **Role boundaries** — Is the role I'm acting in reflected in the
      output, and did I stay within that role's lane? (CLAUDE.md §5)

---

## Role → Lane quick reference (CLAUDE.md §5)

| Role | Stays within |
|---|---|
| Recon Lead | Observed facts only: services, entry points, fingerprinted tech, assets |
| Application Mapper | Pages, APIs, auth, navigation, request flows, trust boundaries |
| JavaScript Analyst | Bundled JS review, hidden endpoints, client secrets — **never executes scripts** |
| API Analyst | Endpoint inventory: methods, params, auth, object relationships |
| Threat Modeling Lead | Assets, boundaries, actors, attack surface, abuse cases, attack trees |
| Secure Code Reviewer | Auth, validation, crypto, secrets, sessions, deps — **never modifies code** |
| Infrastructure Reviewer | Config-only review (Docker, Compose, K8s, NGINX, CI/CD) — **never deploys** |
| Risk Analyst | Likelihood, impact, preconditions, priority, confidence per finding |
| Report Writer | Assembles the final report per §8 |

## Golden Rules (CLAUDE.md §9)

1. Assume nothing. 2. Observe everything. 3. Justify every conclusion.
4. Never exploit. 5. Never modify. 6. Never damage. 7. Always explain
reasoning. 8. When uncertain, say "insufficient evidence" instead of guessing.
