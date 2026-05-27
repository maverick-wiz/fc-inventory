## Pull Request

### Jira Ticket
**Ticket:** [FCINV-XX](https://wizkidtester.atlassian.net/browse/FCINV-XX)

---

## 🟢 OMEGA Self-Certification
<!-- REQUIRED — SAGE will not begin review without this. Check every box. -->
<!-- Copy this block, tick all boxes, and post it as a PR comment when ready. -->

```
🟢 OMEGA SELF-CERT
- [ ] All tests run locally — passing
- [ ] Coverage ≥ 80% on new/changed code
- [ ] ruff + mypy pass with zero errors
- [ ] No secrets, credentials, or hardcoded values committed
- [ ] All DB writes include tenant_id — no unscoped queries
- [ ] SHADOW secure coding standards followed
- [ ] PR is scoped to one ticket only — no scope creep
- [ ] .env.example updated if new config vars added
Signed: OMEGA — {{timestamp}}
```

---

## Summary
<!-- What does this PR do? Be specific. -->


## Type of Change
- [ ] ✨ Feature
- [ ] 🐛 Bug fix
- [ ] 🔒 Security fix
- [ ] ♻️ Refactor
- [ ] 📝 Documentation
- [ ] 🧪 Tests only
- [ ] 🏗️ Infrastructure / CI

## Changes Made
-
-
-

## Test Coverage
- [ ] Unit tests added / updated (`tests/unit/`)
- [ ] Integration tests added / updated (`tests/integration/`)
- [ ] Test IDs mapped to test-cases doc (TC-XXX)
- [ ] Coverage ≥ 80% verified locally

---

## 🔍 SAGE Review Section
<!-- Do not fill this — SAGE will populate after you post self-cert -->

| Category | Status | Notes |
|---|---|---|
| 1. Architecture & Design | ⏳ Pending | — |
| 2. Code Quality | ⏳ Pending | — |
| 3. Security | ⏳ Pending | — |
| 4. Test Coverage | ⏳ Pending | — |
| 5. Performance | ⏳ Pending | — |
| 6. Documentation | ⏳ Pending | — |
| 7. Domain Rules | ⏳ Pending | — |

**SAGE Verdict:** ⏳ Pending self-certification

---

## ✅ Approval Flow

```
OMEGA self-cert posted
    ↓
SAGE auto-gate passes (structure + static checks)
    ↓
Maverick dispatches: "SAGE review FCINV-XX"
    ↓
SAGE posts full signed review report
    ↓
Maverick approves on GitHub → PR merges
```

---
*Branch convention: `feature/FCINV-XX-short-description`*
*PR title convention: `FCINV-XX: what this does`*
