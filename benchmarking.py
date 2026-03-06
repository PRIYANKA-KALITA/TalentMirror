from __future__ import annotations
import math
from typing import Dict

# Synthetic baselines (mean, std) — OK for a college demo.
BASELINES = {
    "backend": {
        "technical_depth": (62, 12),
        "problem_solving": (60, 12),
        "system_design": (55, 14),
        "communication": (58, 12),
        "role_fit": (60, 12),
    },
    "frontend": {
        "technical_depth": (60, 12),
        "problem_solving": (58, 12),
        "system_design": (52, 14),
        "communication": (60, 12),
        "role_fit": (60, 12),
    },
    "fullstack": {
        "technical_depth": (60, 12),
        "problem_solving": (60, 12),
        "system_design": (56, 14),
        "communication": (58, 12),
        "role_fit": (60, 12),
    },
    "data": {
        "technical_depth": (58, 13),
        "problem_solving": (58, 13),
        "system_design": (52, 14),
        "communication": (56, 12),
        "role_fit": (58, 13),
    },
    "devops": {
        "technical_depth": (60, 13),
        "problem_solving": (60, 13),
        "system_design": (58, 14),
        "communication": (56, 12),
        "role_fit": (60, 13),
    },
    "aiml": {  # ✅ added
        "technical_depth": (60, 13),
        "problem_solving": (62, 12),
        "system_design": (55, 14),
        "communication": (56, 12),
        "role_fit": (60, 13),
    },
}

def compute_benchmark(competency_scores: Dict[str, int], role_target: str) -> Dict:
    baseline = BASELINES.get(role_target, BASELINES["fullstack"])
    out = {"role_target": role_target, "percentiles": {}, "explain": {}}

    for comp, score in competency_scores.items():
        mu, sigma = baseline.get(comp, (60, 12))
        pct = _percentile_normal(score, mu, sigma)
        out["percentiles"][comp] = int(round(pct))
        out["explain"][comp] = _band_text(pct)

    overall = sum(out["percentiles"].values()) / max(len(out["percentiles"]), 1)
    out["overall_percentile_estimate"] = int(round(overall))
    out["note"] = (
        "Benchmarking uses a synthetic baseline distribution for a college project. "
        "Replace BASELINES with real data (e.g., collected scoring distributions) for accuracy."
    )
    return out

def _percentile_normal(x: float, mu: float, sigma: float) -> float:
    if sigma <= 1e-9:
        return 50.0
    z = (x - mu) / (sigma * math.sqrt(2))
    cdf = 0.5 * (1 + math.erf(z))
    return max(1.0, min(99.0, 100.0 * cdf))

def _band_text(p: float) -> str:
    if p >= 85:
        return "Top band (well above typical peers)"
    if p >= 65:
        return "Above average"
    if p >= 35:
        return "Around average"
    if p >= 15:
        return "Below average"
    return "Low band (needs improvement)"