---
name: loan-underwriting-metrics
description: Computes and verifies loan underwriting metrics (EMI, DTI, FOIR, net disposable income, LTV, credit utilization, income trend, delinquency, enquiries) deterministically against credit policy thresholds, and cross-checks applicant documents for inconsistencies and fraud signals. Use this skill for EVERY loan application, credit assessment, or underwriting request before stating any ratio, pass/fail result, or recommendation, even when the numbers look simple to calculate mentally. Also use it when the user asks to recheck, recalculate, or explain an underwriting figure.
---

# Loan Underwriting Metrics

This skill makes underwriting numbers reliable. Ratios like DTI and LTV drive the recommendation, and a single arithmetic slip can flip a decision. Every figure you report must come from this skill's calculation steps, not from mental math.

## Workflow

### Step 1: Normalise the input
Map the application data to the fields below. Convert all amounts to monthly figures in one currency (annual ÷ 12). Leave a field out if it is not provided. Never fill gaps with estimates.

| Field | Meaning |
|---|---|
| gross_monthly_income | Gross monthly income |
| net_monthly_income | Take-home monthly income |
| existing_monthly_emis | Sum of all current EMIs, including hidden obligations found in statements |
| loan_amount, interest_rate_pct, tenure_months | Requested loan terms |
| proposed_emi | Only if given in the application |
| loan_type | home_loan, loan_against_property, auto_loan, gold_loan, personal_loan, business_loan |
| secured, collateral_value | Secured loan flag and assessed collateral value |
| credit_score | Bureau score |
| credit_utilization_pct, or revolving_balance and revolving_limit | Card/revolving utilization |
| hard_enquiries_6m | Hard enquiries in last 6 months |
| max_dpd_24m | Worst days-past-due in last 24 months (0 if clean) |
| writeoff_or_settlement_24m | true/false |
| employment_type, employment_months | salaried or self_employed; tenure or business vintage in months |
| monthly_income_history | List of monthly income/credits, oldest first |
| bounces_6m | Bounced cheques / failed debits in last 6 months |

### Step 2: Compute
If code execution is available, run:

```
python scripts/underwriting_metrics.py input.json
```

The script reads thresholds from `references/policy_thresholds.json`. If the knowledge base contains the lender's credit policy and its thresholds differ, the policy document takes precedence. State which threshold you applied.

If code execution is NOT available, compute manually using exactly these formulas and show every step:
- EMI = P × r × (1+r)^n / ((1+r)^n − 1), where r = annual rate ÷ 12 ÷ 100 and n = tenure in months
- DTI = (existing EMIs + proposed EMI) ÷ gross monthly income × 100
- FOIR = (existing EMIs + proposed EMI) ÷ net monthly income × 100
- Net disposable income = net monthly income − existing EMIs − proposed EMI
- LTV = loan amount ÷ collateral value × 100
- Income trend = (latest − earliest) ÷ earliest × 100

Then verify each manual result by recomputing it a second time in a different order. For EMI, check that EMI × n exceeds P and that the implied total interest is plausible for the rate. If the two results disagree, recompute before reporting.

### Step 3: Cross-check documents
When documents or statements are provided, read `references/red_flags.md` and run every applicable check. If you find hidden obligations, add them to existing_monthly_emis and recompute DTI and FOIR. If declared and verified income differ beyond tolerance, use the lower verified figure.

### Step 4: Report
- Present the metrics as a table of Metric, Value, Formula with actual numbers, Threshold, and Result (Pass / Borderline / Fail / Not computable).
- Round currency to the nearest whole unit and ratios to one decimal place.
- Carry every red flag from the script output and the document checks into the Risks & Red Flags section.
- Two or more "Not computable" core metrics, or any mandatory-referral flag, means the recommendation must be "Refer to Human Underwriter".

## Rules
- Never report a ratio without its formula and inputs.
- Never treat a missing metric as a pass.
- If a provided EMI differs from the recalculated EMI by more than 2%, report both and flag the discrepancy.
- Do not use protected attributes (gender, religion, caste, ethnicity, marital status, disability, nationality) in any calculation or check.
