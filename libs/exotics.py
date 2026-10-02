"""
Options exotiques (path-dependent) — pricing Monte Carlo.

Rappel :
  ExerciseStyle (dans option.py) = européen / américain (quand on exerce)
  Ici = type de payoff path-dependent (asian, barrier, ...)
  → une classe par produit, pas un mega-enum de payoffs mélangés.
"""

from enum import Enum

import numpy as np

from libs.montecarlo import discount_mean_payoff, simulate_gbm_paths
from libs.option import ExerciseStyle, Option, OptionType

class AsianAverage(Enum):
    ARITHMETIC = "arithmetic"
    GEOMETRIC = "geometric"


class BarrierType(Enum):
    UP_AND_OUT = "up_and_out"
    UP_AND_IN = "up_and_in"
    DOWN_AND_OUT = "down_and_out"
    DOWN_AND_IN = "down_and_in"


class LookbackType(Enum):
    FIXED_STRIKE = "fixed_strike"      # max(S_max - K, 0) pour un call
    FLOATING_STRIKE = "floating_strike"  # max(S_T - S_min, 0) pour un call


def _vanilla_payoff(ST: np.ndarray, K: float, option_type: OptionType) -> np.ndarray:
    if option_type == OptionType.CALL:
        return np.maximum(ST - K, 0.0)
    return np.maximum(K - ST, 0.0)


class AsianOption(Option):
    """Call/put asiatique : payoff sur la moyenne du chemin."""

    def __init__(
        self,
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float,
        option_type: OptionType,
        average: AsianAverage = AsianAverage.ARITHMETIC,
        *,
        n_paths: int = 50_000,
        n_steps: int = 252,
        seed: int | None = 42,
    ):
        super().__init__(S, K, T, r, sigma, option_type, ExerciseStyle.EUROPEAN)
        self.average = average
        self.n_paths = n_paths
        self.n_steps = n_steps
        self.seed = seed

    def with_spot(self, S: float) -> "AsianOption":
        return AsianOption(
            S, self.K, self.T, self.r, self.sigma, self.option_type, self.average,
            n_paths=self.n_paths, n_steps=self.n_steps, seed=self.seed,
        )

    def price(self) -> float:
        if self.T <= 0:
            return self.payoff()

        paths = simulate_gbm_paths(
            self.S, self.T, self.r, self.sigma,
            n_paths=self.n_paths, n_steps=self.n_steps, seed=self.seed,
        )
        if self.average == AsianAverage.ARITHMETIC:
            A = paths.mean(axis=1)
        else:
            A = np.exp(np.mean(np.log(paths), axis=1))

        payoffs = _vanilla_payoff(A, self.K, self.option_type)
        return discount_mean_payoff(payoffs, self.r, self.T)


class DigitalOption(Option):
    """Cash-or-nothing : paie `cash` si ITM à T, sinon 0."""

    def __init__(
        self,
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float,
        option_type: OptionType,
        cash: float = 1.0,
        *,
        n_paths: int = 50_000,
        n_steps: int = 252,
        seed: int | None = 42,
    ):
        super().__init__(S, K, T, r, sigma, option_type, ExerciseStyle.EUROPEAN)
        self.cash = cash
        self.n_paths = n_paths
        self.n_steps = n_steps
        self.seed = seed

    def with_spot(self, S: float) -> "DigitalOption":
        return DigitalOption(
            S, self.K, self.T, self.r, self.sigma, self.option_type, self.cash,
            n_paths=self.n_paths, n_steps=self.n_steps, seed=self.seed,
        )

    def price(self) -> float:
        if self.T <= 0:
            itm = (self.S >= self.K) if self.option_type == OptionType.CALL else (self.S <= self.K)
            return self.cash if itm else 0.0

        paths = simulate_gbm_paths(
            self.S, self.T, self.r, self.sigma,
            n_paths=self.n_paths, n_steps=self.n_steps, seed=self.seed,
        )
        ST = paths[:, -1]
        if self.option_type == OptionType.CALL:
            payoffs = self.cash * (ST > self.K)
        else:
            payoffs = self.cash * (ST < self.K)
        return discount_mean_payoff(payoffs, self.r, self.T)


class BarrierOption(Option):
    """Barrier européenne (knock-in / knock-out) sur le max/min du chemin."""

    def __init__(
        self,
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float,
        option_type: OptionType,
        barrier: float,
        barrier_type: BarrierType,
        *,
        n_paths: int = 50_000,
        n_steps: int = 252,
        seed: int | None = 42,
    ):
        super().__init__(S, K, T, r, sigma, option_type, ExerciseStyle.EUROPEAN)
        self.barrier = barrier
        self.barrier_type = barrier_type
        self.n_paths = n_paths
        self.n_steps = n_steps
        self.seed = seed

    def with_spot(self, S: float) -> "BarrierOption":
        return BarrierOption(
            S, self.K, self.T, self.r, self.sigma, self.option_type,
            self.barrier, self.barrier_type,
            n_paths=self.n_paths, n_steps=self.n_steps, seed=self.seed,
        )

    def price(self) -> float:
        if self.T <= 0:
            return self.payoff()

        paths = simulate_gbm_paths(
            self.S, self.T, self.r, self.sigma,
            n_paths=self.n_paths, n_steps=self.n_steps, seed=self.seed,
        )
        ST = paths[:, -1]
        hit_up = paths.max(axis=1) >= self.barrier
        hit_down = paths.min(axis=1) <= self.barrier
        vanilla = _vanilla_payoff(ST, self.K, self.option_type)

        bt = self.barrier_type
        if bt == BarrierType.UP_AND_OUT:
            active = ~hit_up
        elif bt == BarrierType.UP_AND_IN:
            active = hit_up
        elif bt == BarrierType.DOWN_AND_OUT:
            active = ~hit_down
        else:  # DOWN_AND_IN
            active = hit_down

        return discount_mean_payoff(vanilla * active, self.r, self.T)


class LookbackOption(Option):
    """Lookback fixed ou floating strike."""

    def __init__(
        self,
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float,
        option_type: OptionType,
        lookback: LookbackType = LookbackType.FIXED_STRIKE,
        *,
        n_paths: int = 50_000,
        n_steps: int = 252,
        seed: int | None = 42,
    ):
        super().__init__(S, K, T, r, sigma, option_type, ExerciseStyle.EUROPEAN)
        self.lookback = lookback
        self.n_paths = n_paths
        self.n_steps = n_steps
        self.seed = seed

    def with_spot(self, S: float) -> "LookbackOption":
        return LookbackOption(
            S, self.K, self.T, self.r, self.sigma, self.option_type, self.lookback,
            n_paths=self.n_paths, n_steps=self.n_steps, seed=self.seed,
        )

    def price(self) -> float:
        if self.T <= 0:
            return self.payoff()

        paths = simulate_gbm_paths(
            self.S, self.T, self.r, self.sigma,
            n_paths=self.n_paths, n_steps=self.n_steps, seed=self.seed,
        )
        ST = paths[:, -1]
        S_max = paths.max(axis=1)
        S_min = paths.min(axis=1)

        if self.lookback == LookbackType.FIXED_STRIKE:
            ref = S_max if self.option_type == OptionType.CALL else S_min
            payoffs = _vanilla_payoff(ref, self.K, self.option_type)
        else:
            # floating strike
            if self.option_type == OptionType.CALL:
                payoffs = np.maximum(ST - S_min, 0.0)
            else:
                payoffs = np.maximum(S_max - ST, 0.0)

        return discount_mean_payoff(payoffs, self.r, self.T)
