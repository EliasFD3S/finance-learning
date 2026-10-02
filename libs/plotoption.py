"""Affichage des options et stratégies (séparé du pricing)."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np

from libs.option import Option, OptionType
from libs.optionstrategy import OptionStrategy


def _spot_grid(option: Option, n: int = 200) -> np.ndarray:
    return np.linspace(option.K * 0.5, option.K * 1.5, n)


def _plot_vs_spot(
    S_range: np.ndarray,
    values,
    *,
    K: float,
    ylabel: str,
    title: str,
    label: str,
):
    plt.plot(S_range, values, label=label)
    plt.axvline(K, linestyle="--", color="gray", label=f"Strike K={K}")
    plt.axhline(0, color="black", linewidth=0.8)
    plt.xlabel("Prix du sous-jacent (S)")
    plt.ylabel(ylabel)
    plt.title(title)
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.show()


def plot_price(option: Option):
    S_range = _spot_grid(option)
    values = [option.with_spot(S).price() for S in S_range]
    kind = option.option_type.value
    _plot_vs_spot(
        S_range, values, K=option.K, ylabel="Prix", title=f"Prix {kind}", label=f"Prix {kind}"
    )


def plot_payoff(option: Option):
    S_range = _spot_grid(option)
    if option.option_type == OptionType.CALL:
        intrinsic = np.maximum(S_range - option.K, 0.0)
    else:
        intrinsic = np.maximum(option.K - S_range, 0.0)
    pnl = intrinsic - option.price()
    kind = option.option_type.value
    _plot_vs_spot(
        S_range, pnl, K=option.K, ylabel="P&L", title=f"Payoff {kind}", label=f"P&L {kind}"
    )


def plot_delta(option: Option):
    S_range = _spot_grid(option)
    values = [option.with_spot(S).delta() for S in S_range]
    kind = option.option_type.value
    _plot_vs_spot(
        S_range, values, K=option.K, ylabel="Delta", title=f"Delta {kind}", label=f"Delta {kind}"
    )


def plot_gamma(option: Option):
    S_range = _spot_grid(option)
    values = [option.with_spot(S).gamma() for S in S_range]
    kind = option.option_type.value
    _plot_vs_spot(
        S_range, values, K=option.K, ylabel="Gamma", title=f"Gamma {kind}", label=f"Gamma {kind}"
    )


def plot_vega(option: Option):
    S_range = _spot_grid(option)
    values = [option.with_spot(S).vega() for S in S_range]
    kind = option.option_type.value
    _plot_vs_spot(
        S_range, values, K=option.K, ylabel="Vega", title=f"Vega {kind}", label=f"Vega {kind}"
    )


def plot_theta(option: Option):
    S_range = _spot_grid(option)
    values = [option.with_spot(S).theta() for S in S_range]
    kind = option.option_type.value
    _plot_vs_spot(
        S_range, values, K=option.K, ylabel="Theta", title=f"Theta {kind}", label=f"Theta {kind}"
    )


def plot_rho(option: Option):
    S_range = _spot_grid(option)
    values = [option.with_spot(S).rho() for S in S_range]
    kind = option.option_type.value
    _plot_vs_spot(
        S_range, values, K=option.K, ylabel="Rho", title=f"Rho {kind}", label=f"Rho {kind}"
    )


def plot_strategy_payoff(strategy: OptionStrategy):
    strikes = [opt.K for opt in strategy.options]
    S_range = np.linspace(min(strikes) * 0.7, max(strikes) * 1.3, 300)
    pnl = [strategy.payoff_at(S) for S in S_range]

    plt.plot(S_range, pnl, label="P&L stratégie")
    for K in sorted(set(strikes)):
        plt.axvline(K, linestyle="--", alpha=0.5, label=f"K={K}")
    plt.axhline(0, color="black", linewidth=0.8)
    plt.xlabel("Prix du sous-jacent à l'expiration (S)")
    plt.ylabel("P&L")
    plt.title("Payoff de la stratégie")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.show()
