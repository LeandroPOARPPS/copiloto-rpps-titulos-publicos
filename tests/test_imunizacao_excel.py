from src.estrategias import (
    BondInput,
    optimize_maximum_convexity,
    optimize_minimum_risk,
)


BONDS = [
    BondInput(
        name="NTN-B 2040",
        maturity_business_days=3744.0,
        duration_business_days=2440.000594617005,
        convexity=119.39892762741314,
    ),
    BondInput(
        name="NTN-B 2045",
        maturity_business_days=4943.0,
        duration_business_days=2784.286863834535,
        convexity=168.40889509561174,
    ),
    BondInput(
        name="NTN-B 2050",
        maturity_business_days=6266.0,
        duration_business_days=3132.9141880462025,
        convexity=223.27022769524885,
    ),
]


def test_otimizacao_1_bate_excel():
    result = optimize_minimum_risk(
        bonds=BONDS,
        liability_present_value=50_000_000,
        liability_duration_business_days=3024,
        max_bonds=3,
        concentration_limit=1.0,
    )

    assert abs(result.weights.get("NTN-B 2040", 0.0) - 0.0) < 1e-8
    assert abs(
        result.weights["NTN-B 2045"] - 0.31240863987509127
    ) < 1e-8
    assert abs(
        result.weights["NTN-B 2050"] - 0.687591360124909
    ) < 1e-8
    assert abs(result.portfolio_duration_business_days - 3024) < 1e-8
    assert abs(result.present_value_assets - 50_000_000) < 1e-6


def test_otimizacao_2_bate_excel():
    result = optimize_maximum_convexity(
        bonds=BONDS,
        liability_present_value=50_000_000,
        liability_duration_business_days=3024,
        max_bonds=3,
        concentration_limit=1.0,
    )

    assert abs(
        result.weights["NTN-B 2040"] - 0.1571829291115771
    ) < 1e-8
    assert abs(result.weights.get("NTN-B 2045", 0.0) - 0.0) < 1e-8
    assert abs(
        result.weights["NTN-B 2050"] - 0.8428170708884228
    ) < 1e-8
    assert abs(result.portfolio_duration_business_days - 3024) < 1e-8
    assert abs(result.portfolio_convexity - 206.9434325) < 1e-6
    assert abs(result.present_value_assets - 50_000_000) < 1e-6
