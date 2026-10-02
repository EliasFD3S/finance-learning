"""Simulation GBM et pricing Monte Carlo (américain + path-dependent)."""

import numpy as np

from libs.option import OptionType


def simulate_gbm_paths(
    S0: float,
    T: float,
    r: float,
    sigma: float,
    *,
    n_paths: int = 50_000,
    n_steps: int = 252,
    seed: int | None = 42,
) -> np.ndarray:
    """Retourne paths de shape (n_paths, n_steps + 1), colonnes = temps."""
    dt = T / n_steps
    rng = np.random.default_rng(seed)
    paths = np.empty((n_paths, n_steps + 1))
    paths[:, 0] = S0
    for j in range(n_steps):
        z = rng.standard_normal(n_paths)
        paths[:, j + 1] = paths[:, j] * np.exp(
            (r - 0.5 * sigma**2) * dt + sigma * np.sqrt(dt) * z
        )
    return paths


def _intrinsic(S: np.ndarray, K: float, option_type: OptionType) -> np.ndarray:
    if option_type == OptionType.CALL:
        return np.maximum(S - K, 0.0)
    return np.maximum(K - S, 0.0)


def price_american_lsm(
    S0: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
    option_type: OptionType,
    *,
    n_paths: int = 50_000,
    n_steps: int = 252,
    seed: int | None = 42,
) -> float:
    """Option américaine via Longstaff–Schwartz."""
    if T <= 0 or sigma <= 0:
        return float(_intrinsic(np.array([S0]), K, option_type)[0])

    dt = T / n_steps
    disc = np.exp(-r * dt)
    paths = simulate_gbm_paths(
        S0, T, r, sigma, n_paths=n_paths, n_steps=n_steps, seed=seed
    )
    cashflow = _intrinsic(paths[:, -1], K, option_type)

    for t in range(n_steps - 1, 0, -1):
        cashflow *= disc
        S_t = paths[:, t]
        intr = _intrinsic(S_t, K, option_type)
        itm = intr > 0
        if np.count_nonzero(itm) < 20:
            continue

        X = S_t[itm]
        Y = cashflow[itm]
        basis = np.column_stack([np.ones_like(X), X, X**2])
        beta = np.linalg.lstsq(basis, Y, rcond=None)[0]
        continuation = basis @ beta
        exercise = intr[itm] > continuation
        itm_idx = np.flatnonzero(itm)
        cashflow[itm_idx[exercise]] = intr[itm_idx[exercise]]

    cashflow *= disc
    return float(np.mean(cashflow))


def discount_mean_payoff(payoffs: np.ndarray, r: float, T: float) -> float:
    return float(np.exp(-r * T) * np.mean(payoffs))
