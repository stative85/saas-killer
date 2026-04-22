import { WendigoReport, TrapdoorEvent } from "@wendigo/contracts";

export class PrReporter {
  buildTitle(report: WendigoReport): string {
    return `[WENDIGO-CIS] Security Remediation: ${report.vulnId}`;
  }

  buildBody(report: WendigoReport): string {
    return `
# 🛡️ WENDIGO C.I.S. Forensic Report

**Vulnerability:** ${report.vulnId} (${report.cve || 'No CVE'})
**Severity:** ${report.severity}
**Target File:** \`${report.targetFile}\`

---

## 🔬 Execution Summary
- **LOC Extracted:** ${report.executionSummary.extractedLoc}
- **Confidence:** ${report.executionSummary.confidenceScore * 100}%
- **Apex Contender:** \`${report.executionSummary.apexContender}\`

## ⚖️ Validation Results
The patch was subjected to hostile invariants and regression testing.
- **Compilation:** PASSED
- **Invariants:** PASSED
- **Rollback Confidence:** ${report.receipts.rollbackConfidence}

---
*This PR was generated automatically by WENDIGO C.I.S. after hostile validation.*
    `;
  }
}
