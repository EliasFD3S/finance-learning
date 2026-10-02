import numpy as np


def simulate_heston_paths(
    S0: float,
    v0: float,
    r: float,
    kappa: float,
    theta: float,
    xi: float,
    rho: float,
    T: float,
    *,
    n_paths: int = 50_000,
    n_steps: int = 252,
    seed: int | None = 42,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Simulation Heston (Euler + réflexion sur la variance).

    dS_t = r S_t dt + √v_t S_t dW^S
    dv_t = κ(θ − v_t) dt + ξ √v_t dW^v
    corr(dW^S, dW^v) = ρ

    Returns
    -------
    S, v : arrays de shape (n_paths, n_steps + 1)

    Notes
    -----
    Condition de Feller (évite que v atteigne 0 trop souvent) :
        2 κ θ > ξ²
    Le schéma à réflexion reste biasé près de 0 ; OK pour apprendre.
    """
    if not (-1.0 <= rho <= 1.0):
        raise ValueError("rho doit être dans [-1, 1]")
    if T <= 0:
        S = np.full((n_paths, 1), S0, dtype=float)
        v = np.full((n_paths, 1), max(v0, 0.0), dtype=float)
        return S, v

    dt = T / n_steps
    rng = np.random.default_rng(seed)

    S = np.empty((n_paths, n_steps + 1))
    v = np.empty((n_paths, n_steps + 1))
    S[:, 0] = S0
    v[:, 0] = max(v0, 0.0)

    rho_bar = np.sqrt(max(1.0 - rho**2, 0.0))

    for t in range(n_steps):
        Z_S = rng.standard_normal(n_paths)
        Z_indep = rng.standard_normal(n_paths)
        Z_v = rho * Z_S + rho_bar * Z_indep

        v_plus = np.maximum(v[:, t], 0.0)
        sqrt_v_dt = np.sqrt(v_plus * dt)

        v[:, t + 1] = (
            v[:, t]
            + kappa * (theta - v_plus) * dt
            + xi * sqrt_v_dt * Z_v
        )
        v[:, t + 1] = np.maximum(v[:, t + 1], 0.0)

        S[:, t + 1] = S[:, t] * np.exp(
            (r - 0.5 * v_plus) * dt + sqrt_v_dt * Z_S
        )

    return S, v


def feller_ok(kappa: float, theta: float, xi: float) -> bool:
    """True si 2 κ θ > ξ²."""
    return 2.0 * kappa * theta > xi**2
