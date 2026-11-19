#!/usr/bin/env python3
"""
Deterministic loan underwriting metrics calculator.

Usage:
    python underwriting_metrics.py input.json [--policy policy.json]
    echo '{...}' | python underwriting_metrics.py - [--policy policy.json]

All input fields are optional. Missing inputs produce "Not computable" rather
than guesses. Output is JSON with each metric's value, formula, threshold and result.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_POLICY = os.path.join(HERE, "..", "references", "policy_thresholds.json")


def num(x):
    if x is None or x == "":
        return None
    try:
        return float(str(x).replace(",", "").replace("₹", "").replace("%", "").strip())
    except ValueError:
        return None


def nc(name, missing):
    return {"metric": name, "value": None, "result": "Not computable",
            "reason": "Missing: " + ", ".join(missing)}


def emi(principal, annual_rate_pct, months):
    r = annual_rate_pct / 12 / 100
    if r == 0:
        return principal / months
    f = (1 + r) ** months
    return principal * r * f / (f - 1)


def compute(d, p):
    out, flags = [], []
    income = num(d.get("gross_monthly_income"))
    net_income = num(d.get("net_monthly_income"))
    existing = num(d.get("existing_monthly_emis"))
    amt = num(d.get("loan_amount"))
    rate = num(d.get("interest_rate_pct"))
    tenure = num(d.get("tenure_months"))
    given_emi = num(d.get("proposed_emi"))

    # Proposed EMI
    proposed = None
    if given_emi is not None:
        proposed = given_emi
        item = {"metric": "Proposed EMI", "value": round(given_emi), "source": "provided"}
        if None not in (amt, rate, tenure):
            calc = emi(amt, rate, tenure)
            item["recalculated"] = round(calc)
            if abs(calc - given_emi) / calc > 0.02:
                flags.append(f"Provided EMI {round(given_emi)} differs from recalculated {round(calc)} by more than 2%")
        out.append(item)
    elif None not in (amt, rate, tenure):
        proposed = emi(amt, rate, tenure)
        out.append({"metric": "Proposed EMI", "value": round(proposed),
                    "formula": f"P*r*(1+r)^n/((1+r)^n-1), P={amt:.0f}, r={rate}%/12, n={tenure:.0f}"})
    else:
        out.append(nc("Proposed EMI", [k for k, v in
                   {"loan_amount": amt, "interest_rate_pct": rate, "tenure_months": tenure}.items() if v is None]))

    # DTI
    if None not in (income, existing, proposed) and income > 0:
        dti = (existing + proposed) / income * 100
        res = "Pass" if dti <= p["dti_comfort_pct"] else ("Borderline" if dti <= p["dti_max_pct"] else "Fail")
        out.append({"metric": "DTI", "value": round(dti, 1), "unit": "%",
                    "formula": f"({existing:.0f} + {proposed:.0f}) / {income:.0f}",
                    "threshold": f"<= {p['dti_comfort_pct']}% comfortable, <= {p['dti_max_pct']}% max",
                    "result": res})
    else:
        out.append(nc("DTI", [k for k, v in {"gross_monthly_income": income,
                   "existing_monthly_emis": existing, "proposed_emi": proposed}.items() if v is None]))

    # FOIR and net disposable income
    if None not in (net_income, existing, proposed) and net_income > 0:
        foir = (existing + proposed) / net_income * 100
        ndi = net_income - existing - proposed
        out.append({"metric": "FOIR", "value": round(foir, 1), "unit": "%",
                    "formula": f"({existing:.0f} + {proposed:.0f}) / {net_income:.0f}",
                    "threshold": f"<= {p['foir_max_pct']}%",
                    "result": "Pass" if foir <= p["foir_max_pct"] else "Fail"})
        out.append({"metric": "Net disposable income", "value": round(ndi),
                    "formula": f"{net_income:.0f} - {existing:.0f} - {proposed:.0f}",
                    "threshold": f">= {p['min_net_disposable_income']}",
                    "result": "Pass" if ndi >= p["min_net_disposable_income"] else "Fail"})
    else:
        out.append(nc("FOIR / Net disposable income", [k for k, v in {"net_monthly_income": net_income,
                   "existing_monthly_emis": existing, "proposed_emi": proposed}.items() if v is None]))

    # Credit score
    score = num(d.get("credit_score"))
    if score is not None:
        cs = p["credit_score"]
        res = "Pass" if score >= cs["standard_min"] else ("Borderline" if score >= cs["borderline_min"] else "Fail")
        out.append({"metric": "Credit score", "value": int(score),
                    "threshold": f">= {cs['standard_min']} (borderline {cs['borderline_min']}-{cs['standard_min']-1})",
                    "result": res})
    else:
        out.append(nc("Credit score", ["credit_score"]))

    # Utilization
    util = num(d.get("credit_utilization_pct"))
    if util is None:
        used, limit = num(d.get("revolving_balance")), num(d.get("revolving_limit"))
        if None not in (used, limit) and limit > 0:
            util = used / limit * 100
    if util is not None:
        out.append({"metric": "Credit utilization", "value": round(util, 1), "unit": "%",
                    "threshold": f"<= {p['credit_utilization_max_pct']}%",
                    "result": "Pass" if util <= p["credit_utilization_max_pct"] else "Fail"})
    else:
        out.append(nc("Credit utilization", ["credit_utilization_pct or revolving_balance+revolving_limit"]))

    # Enquiries
    enq = num(d.get("hard_enquiries_6m"))
    if enq is not None:
        out.append({"metric": "Hard enquiries (6m)", "value": int(enq),
                    "threshold": f"<= {p['hard_enquiries_6m_max']}",
                    "result": "Pass" if enq <= p["hard_enquiries_6m_max"] else "Fail"})
    else:
        out.append(nc("Hard enquiries (6m)", ["hard_enquiries_6m"]))

    # Delinquency
    dpd = d.get("max_dpd_24m")
    if dpd is not None:
        dpdv = num(dpd) or 0
        res = "Pass" if dpdv == 0 else ("Borderline" if dpdv < 60 else "Fail")
        out.append({"metric": "Max DPD (24m)", "value": int(dpdv), "threshold": "0 for auto-approval", "result": res})
        if dpdv >= 90:
            flags.append("90+ DPD in last 24 months: mandatory referral")
    else:
        out.append(nc("Max DPD (24m)", ["max_dpd_24m"]))
    if d.get("writeoff_or_settlement_24m") is True:
        flags.append("Write-off or settlement in last 24 months: mandatory referral")

    # LTV
    coll = num(d.get("collateral_value"))
    if coll is not None and amt is not None and coll > 0:
        ltv = amt / coll * 100
        cap = p["ltv_max_pct"].get(d.get("loan_type", ""), p["ltv_max_pct"]["default"])
        out.append({"metric": "LTV", "value": round(ltv, 1), "unit": "%",
                    "formula": f"{amt:.0f} / {coll:.0f}", "threshold": f"<= {cap}%",
                    "result": "Pass" if ltv <= cap else "Fail"})
    elif d.get("secured") is True:
        out.append(nc("LTV", [k for k, v in {"loan_amount": amt, "collateral_value": coll}.items() if v is None]))

    # Income trend
    hist = d.get("monthly_income_history")
    if isinstance(hist, list) and len(hist) >= 2:
        vals = [num(v) for v in hist if num(v) is not None]
        if len(vals) >= 2 and vals[0] > 0:
            chg = (vals[-1] - vals[0]) / vals[0] * 100
            out.append({"metric": "Income trend", "value": round(chg, 1), "unit": "%",
                        "formula": f"(latest {vals[-1]:.0f} - earliest {vals[0]:.0f}) / earliest",
                        "threshold": f"decline <= {p['income_decline_flag_pct']}%",
                        "result": "Fail" if chg < -p["income_decline_flag_pct"] else "Pass"})
            avg = sum(vals) / len(vals)
            if income is not None and avg > 0 and abs(income - avg) / avg > 0.15:
                flags.append(f"Declared income {income:.0f} differs from statement average {avg:.0f} by more than 15%")

    # Employment / vintage
    tenure_emp = num(d.get("employment_months"))
    if tenure_emp is not None:
        st = d.get("employment_type", "salaried")
        lim = p["min_business_vintage_months"] if st == "self_employed" else p["min_employment_months_salaried"]
        out.append({"metric": "Employment tenure / business vintage", "value": int(tenure_emp), "unit": "months",
                    "threshold": f">= {lim}", "result": "Pass" if tenure_emp >= lim else "Fail"})

    # Bounces
    b = num(d.get("bounces_6m"))
    if b is not None:
        out.append({"metric": "Bounces / failed debits (6m)", "value": int(b),
                    "threshold": f"<= {p['max_bounces_6m']}",
                    "result": "Pass" if b <= p["max_bounces_6m"] else "Fail"})

    if amt is not None and amt > p["auto_decision_max_loan_amount"]:
        flags.append(f"Loan amount {amt:.0f} exceeds auto-decision limit {p['auto_decision_max_loan_amount']}")

    missing = sum(1 for m in out if m.get("result") == "Not computable")
    if missing >= 2:
        flags.append(f"{missing} metrics not computable: referral likely required")

    return {"metrics": out, "red_flags": flags,
            "summary": {k: sum(1 for m in out if m.get("result") == k)
                        for k in ("Pass", "Borderline", "Fail", "Not computable")}}


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(1)
    policy_path = DEFAULT_POLICY
    if "--policy" in args:
        policy_path = args[args.index("--policy") + 1]
    src = args[0]
    data = json.load(sys.stdin) if src == "-" else json.load(open(src))
    policy = json.load(open(policy_path))
    print(json.dumps(compute(data, policy), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
