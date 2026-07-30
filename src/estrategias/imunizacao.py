from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from math import isclose
from typing import Iterable

import numpy as np
from scipy.optimize import linprog


@dataclass(frozen=True)
class BondInput:
    name: str
    maturity_business_days: float
    duration_business_days: float
    convexity: float
    pu: float | None = None


@dataclass(frozen=True)
class ImmunizationResult:
    objective: str
    weights: dict[str, float]
    portfolio_duration_business_days: float
    portfolio_convexity: float
    portfolio_risk_measure: float
    present_value_assets: float
    present_value_liability: float
    quantities: dict[str, float]
    selected_bonds: tuple[str, ...]


def _validate_inputs(
    bonds: list[BondInput],
    liability_present_value: float,
    liability_duration_business_days: float,
    max_bonds: int,
    concentration_limit: float,
) -> None:
    if not bonds:
        raise ValueError("A lista de títulos não pode estar vazia.")
    if liability_present_value <= 0:
        raise ValueError("O valor presente do passivo deve ser positivo.")
    if liability_duration_business_days <= 0:
        raise ValueError("A duration do passivo deve ser positiva.")
    if max_bonds < 1:
        raise ValueError("max_bonds deve ser pelo menos 1.")
    if not 0 < concentration_limit <= 1:
        raise ValueError("concentration_limit deve estar entre 0 e 1.")
    if max_bonds * concentration_limit < 1 - 1e-12:
        raise ValueError(
            "A combinação de máximo de títulos e limite de concentração "
            "não permite somar 100%."
        )


def _solve_subset(
    subset: tuple[BondInput, ...],
    liability_duration_business_days: float,
    concentration_limit: float,
    objective: str,
):
    durations = np.array(
        [bond.duration_business_days for bond in subset], dtype=float
    )
    convexities = np.array([bond.convexity for bond in subset], dtype=float)
    risks = np.array(
        [
            abs(
                bond.maturity_business_days
                - bond.duration_business_days
            )
            for bond in subset
        ],
        dtype=float,
    )

    if objective == "minimum_risk":
        c = risks
    elif objective == "maximum_convexity":
        c = -convexities
    else:
        raise ValueError(f"Objetivo desconhecido: {objective}")

    a_eq = np.vstack([np.ones(len(subset)), durations])
    b_eq = np.array([1.0, liability_duration_business_days], dtype=float)
    bounds = [(0.0, concentration_limit) for _ in subset]

    result = linprog(
        c=c,
        A_eq=a_eq,
        b_eq=b_eq,
        bounds=bounds,
        method="highs",
    )

    if not result.success:
        return None

    weights = np.where(np.abs(result.x) < 1e-12, 0.0, result.x)
    return weights, risks, convexities


def _optimize(
    bonds: Iterable[BondInput],
    liability_present_value: float,
    liability_duration_business_days: float,
    max_bonds: int,
    concentration_limit: float,
    objective: str,
    minimum_weight: float = 1e-10,
) -> ImmunizationResult:
    bonds = list(bonds)
    _validate_inputs(
        bonds,
        liability_present_value,
        liability_duration_business_days,
        max_bonds,
        concentration_limit,
    )

    best = None

    for size in range(1, min(max_bonds, len(bonds)) + 1):
        for subset in combinations(bonds, size):
            solution = _solve_subset(
                subset,
                liability_duration_business_days,
                concentration_limit,
                objective,
            )
            if solution is None:
                continue

            weights, risks, convexities = solution
            active = weights > minimum_weight

            if active.sum() == 0 or active.sum() > max_bonds:
                continue

            score = (
                float(np.dot(weights, risks))
                if objective == "minimum_risk"
                else float(np.dot(weights, convexities))
            )

            if best is None:
                best = (score, subset, weights, risks, convexities)
            elif objective == "minimum_risk" and score < best[0] - 1e-10:
                best = (score, subset, weights, risks, convexities)
            elif objective == "maximum_convexity" and score > best[0] + 1e-10:
                best = (score, subset, weights, risks, convexities)

    if best is None:
        raise ValueError(
            "Não existe carteira viável com as restrições informadas."
        )

    _, subset, weights, risks, convexities = best

    weights_map = {
        bond.name: float(weight)
        for bond, weight in zip(subset, weights)
        if weight > minimum_weight
    }

    duration = sum(
        bond.duration_business_days * weight
        for bond, weight in zip(subset, weights)
    )
    convexity = sum(
        bond.convexity * weight
        for bond, weight in zip(subset, weights)
    )
    risk_measure = sum(
        risk * weight for risk, weight in zip(risks, weights)
    )

    quantities: dict[str, float] = {}
    for bond, weight in zip(subset, weights):
        if weight <= minimum_weight:
            continue
        if bond.pu is None or bond.pu <= 0:
            quantities[bond.name] = float("nan")
        else:
            quantities[bond.name] = (
                liability_present_value * float(weight) / bond.pu
            )

    present_value_assets = liability_present_value * sum(weights_map.values())

    return ImmunizationResult(
        objective=objective,
        weights=weights_map,
        portfolio_duration_business_days=float(duration),
        portfolio_convexity=float(convexity),
        portfolio_risk_measure=float(risk_measure),
        present_value_assets=float(present_value_assets),
        present_value_liability=float(liability_present_value),
        quantities=quantities,
        selected_bonds=tuple(weights_map.keys()),
    )


def optimize_minimum_risk(
    bonds: Iterable[BondInput],
    liability_present_value: float,
    liability_duration_business_days: float,
    max_bonds: int = 5,
    concentration_limit: float = 1.0,
) -> ImmunizationResult:
    return _optimize(
        bonds=bonds,
        liability_present_value=liability_present_value,
        liability_duration_business_days=liability_duration_business_days,
        max_bonds=max_bonds,
        concentration_limit=concentration_limit,
        objective="minimum_risk",
    )


def optimize_maximum_convexity(
    bonds: Iterable[BondInput],
    liability_present_value: float,
    liability_duration_business_days: float,
    max_bonds: int = 5,
    concentration_limit: float = 1.0,
) -> ImmunizationResult:
    return _optimize(
        bonds=bonds,
        liability_present_value=liability_present_value,
        liability_duration_business_days=liability_duration_business_days,
        max_bonds=max_bonds,
        concentration_limit=concentration_limit,
        objective="maximum_convexity",
    )
