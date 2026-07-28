<!--
Full Assessment Report — implements CLAUDE.md §8 (Report Format).

Sections MUST appear in this order. Every conclusion must trace to an
observation made in this session (CLAUDE.md §3, §9). When a section has no
evidence, write "insufficient evidence" rather than guessing.
-->

# AI Red Team Lab — Assessment Report

**Assessment date:** <YYYY-MM-DD>
**Assessor:** <role(s)>
**Environment:** <local lab identifier>

---

## 1. Executive Summary
<Plain-language overview: what was assessed, the headline findings, and the
overall risk posture. 1–3 paragraphs. No jargon. Evidence-backed only.>

## 2. Scope
<Exactly what was in-scope: host(s), port range, repo, container, or URL.
State what was explicitly out-of-scope. If scope was ambiguous, note the
clarification that resolved it (CLAUDE.md §1, §12).>

## 3. Architecture Understanding
<How the system is put together, as observed: components, how they connect,
request flow. Diagram or bullet the data path. Facts only.>

## 4. Technology Stack
<Fingerprinted technologies with the evidence that identified each
(banner, header, file, dependency manifest). Mark inferred vs. confirmed.>

## 5. Asset Inventory
<Exposed services, entry points, pages, APIs, files, and data stores
discovered this session.>

| Asset | Type | Location | How observed |
|---|---|---|---|
| <name> | <service/page/api/file> | <host:port / path> | <evidence> |

## 6. Trust Boundaries
<Where privilege or trust changes hands: unauthenticated → authenticated,
client → server, app → database, container → host. Identify each boundary
and what crosses it.>

## 7. Attack Surface
<The reachable inputs an actor could influence: parameters, headers, forms,
APIs, file uploads, redirects. Group by entry point.>

## 8. Findings
<One finding card per issue (see templates/finding-card.md). Each MUST carry
all 8 evidence fields, a Risk Rating (Confidence), and a non-destructive
Recommended Validation. Order by severity.>

<!-- paste finding cards here -->

## 9. Secure Design Improvements
<Design-level changes that would remove classes of the findings above, not
just individual bugs.>

## 10. Hardening Roadmap
<Prioritized, sequenced remediation. Group by effort/impact.>

| Priority | Action | Addresses | Effort |
|---|---|---|---|
| <P1> | <change> | <F-NN…> | <S/M/L> |

## 11. Remaining Unknowns
<Everything not verified: unreached endpoints, unconfirmed hypotheses,
gaps in evidence. List them — do not silently assume they are fine.>

## 12. Questions for the Owner
<Open questions whose answers would change the assessment: intended trust
model, expected auth, data sensitivity, deployment context.>
