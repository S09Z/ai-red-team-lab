<!--
Finding Card — implements CLAUDE.md §6 (Evidence Requirements).

Every finding MUST include all 8 fields below. If any field is weak or
missing, state that explicitly (e.g. "insufficient evidence") rather than
filling the gap with inference. Copy this card once per finding into the
report's §8 Findings section.
-->

## Finding: <short descriptive title>

**ID:** F-<NN>
**Confidence:** <Critical | High | Medium | Low | Informational>
**Role:** <Recon Lead | Application Mapper | JavaScript Analyst | API Analyst | Threat Modeling Lead | Secure Code Reviewer | Infrastructure Reviewer | Risk Analyst>

### 1. Observation
<What was observed in *this* session. State the plain fact, no interpretation.>

### 2. Evidence
<The concrete artifact supporting the observation: request/response excerpt,
file path + line, config snippet, header dump, log line. Quote it verbatim.>

```
<paste evidence here — verbatim, trimmed to what matters>
```

### 3. Reasoning
<Why the evidence leads to the conclusion. Show the chain of inference; do
not skip steps.>

### 4. Confidence
<Restate the rating and justify it against the evidence shown. Use the scale:
- Critical — only if evidence strongly supports severe risk
- High — strong evidence
- Medium — reasonable evidence
- Low — possible issue requiring validation
- Informational — no security impact
Never overstate certainty.>

### 5. Possible Impact
<What could go wrong if the issue is real. Business + technical impact.>

### 6. Suggested Validation
<Non-destructive validation only (CLAUDE.md §7): configuration review, source
code review, logging review, manual verification, unit tests, integration
tests, or security regression tests. Never validate by exploiting.>

### 7. Recommended Fix
<Concrete remediation. Prefer specific, testable changes over generic advice.>

### 8. Unknowns
<What remains unverified or out of scope for this finding. List open items
rather than assuming they are fine.>
