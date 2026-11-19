# Document Cross-Verification & Red Flag Checklist

Run each check only when the relevant documents or data are present. Record every check as Passed, Failed (with evidence), or Not checked (data missing).

## Identity & KYC consistency
- Name, date of birth, and address match across ID proof, PAN/tax ID, bank statements, and application.
- Minor spelling variants are acceptable. Different names, DOBs, or ID numbers are a Failed check.
- The ID number format is valid for its type. Flag malformed IDs, but do not attempt to validate against external registries.

## Income consistency
- Salary slip net pay should match the salary credit in bank statements within ±5%.
- Gross income on slips should be consistent with ITR / Form 16 annual income (annual ÷ 12, within ±15%).
- Employer name on slips should match the bank statement salary credit narration.
- Self-employed: declared monthly income should be roughly consistent with average monthly business credits in statements.

## Fabrication signals
- Round-figure income (e.g., exactly 1,00,000) with no matching bank credits.
- Salary credited in cash or through a different account than declared.
- Large one-off deposits shortly before the application with no explained source ("window dressing").
- Balance pattern where funds arrive and leave within 1–2 days repeatedly (circular transactions).
- Statement period, bank formatting, or running balances that do not add up.

## Hidden obligations
- Recurring debits in bank statements (EMIs, NACH mandates, standing instructions) that are NOT listed in declared obligations or the credit report. Add these to existing EMIs for DTI and note the discrepancy.
- Payments to digital lending apps or BNPL providers.

## Banking behaviour
- Cheque / NACH / ECS bounces, especially "insufficient funds".
- Average monthly balance consistently below the proposed EMI.
- Frequent overdraft usage or negative balances.

## Collateral (secured loans)
- Valuation older than 6 months: request revaluation.
- Owner name on property documents differs from applicant / co-applicant.
- Any mention of existing lien, mortgage, or litigation.

## Severity mapping
| Finding | Action |
|---|---|
| Identity mismatch, fabrication signal, circular transactions | Refer to Human Underwriter (possible fraud) |
| Hidden obligations | Recompute DTI including them; refer if DTI then fails |
| Income mismatch > tolerance | Use the LOWER verified figure for all ratios; note it |
| Minor bounces (1) with explanation | Note as a risk, do not auto-refer |
| Stale valuation | Add as a condition |
