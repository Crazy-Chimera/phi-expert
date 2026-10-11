"""Formula catalog and guarded numerical helpers for the supplied Φ-theory model.

The catalog records proposed expressions, not established scientific results.
"""
from __future__ import annotations
import math
from typing import Any
import numpy as np

PLANCK_LENGTH = 1.616255e-35
PLANCK_VOLUME = PLANCK_LENGTH ** 3
HBAR = 1.054571817e-34
C_LIGHT = 299792458.0

FORMULA_CATEGORIES: dict[str, list[dict[str, str]]] = {
 "A":[
  {"id":"A.1","name":"Information field","equation":"Φ = Σᵢⱼ Iᵢⱼ / Vₚ","meaning":"Proposed information field from pairwise information and Planck volume.","status":"normalization and units require definition"},
  {"id":"A.2","name":"Information distance","equation":"d = lₚ / Iᵢⱼ","meaning":"Proposed distance-like relation.","status":"not a standard distance; information units must be specified"}],
 "B":[
  {"id":"B.1","name":"Metric correction","equation":"gᵤᵥ = ηᵤᵥ + α(∇ᵤ∇ᵥΦ − ¼ηᵤᵥ□Φ)","meaning":"Schematic correction to a base metric.","status":"requires derivation and physical dimensions"}],
 "C":[
  {"id":"C.1","name":"Action density proxy","equation":"L = ½(∂Φ)² − V(Φ) + λC","meaning":"Proposed scalar Lagrangian-density form.","status":"field derivatives and units are underspecified"}],
 "D":[
  {"id":"D.1","name":"Elegance","equation":"E = C/K","meaning":"Complexity relative to consistency.","status":"definitions and measurement protocol required"}],
 "E":[
  {"id":"E.1","name":"Information force","equation":"Fᵢₙfₒ = −γ∇C","meaning":"Proposed force-like term.","status":"speculative; dimensional consistency required"}],
 "F":[
  {"id":"F.1","name":"Mass from complexity rate","equation":"m = (ħ/c²)·dC/dt","meaning":"Proposed mass-like mapping.","status":"units depend on the definition of C"}],
 "G":[
  {"id":"G.1","name":"Effective cosmological term","equation":"Λ = dV/dΦ when K < 1; Λ = 0 at K = 1","meaning":"Conditional proposed potential derivative.","status":"potential V and normalization are unspecified"}],
 "H":[
  {"id":"H.1","name":"Expansion proxy","equation":"H ∝ dC/dt","meaning":"Proposed relationship between expansion and complexity rate.","status":"proportionality and units unspecified"}],
 "I":[
  {"id":"I.1","name":"Collective computation","equation":"Cₙ₊₁ = F(Cₙ)","meaning":"Iterative update abstraction.","status":"operator and state space must be defined"}],
 "J":[
  {"id":"J.1","name":"Resonance","equation":"R = Σᵢ wᵢrᵢ","meaning":"Generic weighted resonance score.","status":"weights and measurements unspecified"}],
 "K":[
  {"id":"K.1","name":"Recursive depth","equation":"R = max{k | I(ρᵏ:ρᵏ⁺¹) > Icrit}","meaning":"Depth of nested representations above a threshold.","status":"operational definitions and estimator required"}],
 "L":[
  {"id":"L.1","name":"Substrate iteration","equation":"Sₙ₊₁ = E(Sₙ)","meaning":"Iterative state update.","status":"algorithmic postulate"}],
 "M":[
  {"id":"M.1","name":"Informion oscillation","equation":"f = mᵢc²/h","meaning":"Proposed oscillation frequency relation.","status":"proposed parameters require independent validation"}],
 "N":[
  {"id":"N.1","name":"Local variation of G","equation":"ΔG/G ≈ 10⁻¹⁰ to 10⁻¹²","meaning":"Proposed local variation.","status":"prediction; precision and timescale unspecified"}],
 "O":[
  {"id":"O.1","name":"Symbol summary","equation":"Φ∈[0,1]; K=1−ρ; C≥0; E=C/K","meaning":"Summary of model variables.","status":"symbols are not all operationally defined"}]
}

def get_formula_catalog() -> dict[str, list[dict[str, str]]]:
    return {k: [dict(x) for x in v] for k, v in FORMULA_CATEGORIES.items()}

def compute_phi(I_ij: Any, V_P: float = PLANCK_VOLUME) -> float:
    values = np.asarray(I_ij, dtype=float)
    volume = float(V_P)
    if values.size == 0 or not np.all(np.isfinite(values)) or np.any(values < 0) or not math.isfinite(volume) or volume <= 0:
        raise ValueError("I_ij must be finite and non-negative; V_P must be finite and positive.")
    return float(values.sum() / volume)

def compute_distance(I_ij: float) -> float:
    value = float(I_ij)
    if not math.isfinite(value) or value < 0:
        raise ValueError("I_ij must be finite and non-negative.")
    return math.inf if value == 0 else PLANCK_LENGTH / value

def compute_elegance(C: float, K: float) -> float:
    c, k = float(C), float(K)
    if not math.isfinite(c) or c < 0 or not math.isfinite(k) or k <= 0:
        raise ValueError("C must be finite and non-negative; K must be finite and greater than zero.")
    return c / k

def compute_mass(dC_dt: float) -> float:
    rate = float(dC_dt)
    if not math.isfinite(rate):
        raise ValueError("dC_dt must be finite.")
    return HBAR * rate / (C_LIGHT ** 2)

def compute_F_info(gamma: float, grad_C: Any) -> list[float]:
    g = float(gamma)
    gradient = np.asarray(grad_C, dtype=float)
    if not math.isfinite(g) or gradient.size == 0 or not np.all(np.isfinite(gradient)):
        raise ValueError("gamma and grad_C must be finite; grad_C must be non-empty.")
    return (-g * gradient).tolist()

def compute_action(phi: float, V: float, C: float, lambda_: float) -> float:
    vals = [float(x) for x in (phi, V, C, lambda_)]
    if not all(math.isfinite(x) for x in vals):
        raise ValueError("All inputs must be finite.")
    field, potential, complexity, multiplier = vals
    return 0.5 * field * field - potential + multiplier * complexity
