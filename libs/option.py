from abc import ABC, abstractmethod
from enum import Enum

import numpy as np
import scipy.stats as stats


class OptionType(Enum):
    CALL = "call"
    PUT = "put"


class ExerciseStyle(Enum):
    EUROPEAN = "european"
    AMERICAN = "american"

class Option(ABC):
    """Base polymorphe : paramètres communs, price() à implémenter."""

    def __init__(
        self,
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float,
        option_type: OptionType,
        exercise_style: ExerciseStyle,
    ):
        self.S = S
        self.K = K
        self.T = T
        self.r = r
        self.sigma = sigma
        self.option_type = option_type
        self.exercise_style = exercise_style

    @abstractmethod
    def price(self) -> float:
        ...

    @abstractmethod
    def with_spot(self, S: float) -> "Option":
        """Même contrat, autre spot (utile pour tracer vs S)."""
        ...

    def payoff(self) -> float:
        if self.option_type == OptionType.CALL:
            return max(self.S - self.K, 0.0)
        return max(self.K - self.S, 0.0)

    def delta(self) -> float:
        raise NotImplementedError(f"delta non implémenté pour {type(self).__name__}")

    def gamma(self) -> float:
        raise NotImplementedError(f"gamma non implémenté pour {type(self).__name__}")

    def vega(self) -> float:
        raise NotImplementedError(f"vega non implémenté pour {type(self).__name__}")

    def theta(self) -> float:
        raise NotImplementedError(f"theta non implémenté pour {type(self).__name__}")

    def rho(self) -> float:
        raise NotImplementedError(f"rho non implémenté pour {type(self).__name__}")


class EuropeanOption(Option):
    """Option européenne : Black–Scholes."""

    def __init__(
        self,
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float,
        option_type: OptionType,
    ):
        super().__init__(S, K, T, r, sigma, option_type, ExerciseStyle.EUROPEAN)

    def with_spot(self, S: float) -> "EuropeanOption":
        return EuropeanOption(S, self.K, self.T, self.r, self.sigma, self.option_type)

    def _d1(self):
        return (np.log(self.S / self.K) + (self.r + 0.5 * self.sigma**2) * self.T) / (
            self.sigma * np.sqrt(self.T)
        )

    def _d2(self):
        return self._d1() - self.sigma * np.sqrt(self.T)

    def price(self) -> float:
        if self.T <= 0 or self.sigma <= 0:
            return self.payoff()

        D1, D2 = self._d1(), self._d2()
        discount = self.K * np.exp(-self.r * self.T)

        if self.option_type == OptionType.CALL:
            return self.S * stats.norm.cdf(D1) - discount * stats.norm.cdf(D2)
        return discount * stats.norm.cdf(-D2) - self.S * stats.norm.cdf(-D1)

    def delta(self) -> float:
        D1 = self._d1()
        if self.option_type == OptionType.CALL:
            return float(stats.norm.cdf(D1))
        return float(stats.norm.cdf(D1) - 1.0)

    def gamma(self) -> float:
        return float(
            stats.norm.pdf(self._d1()) / (self.S * self.sigma * np.sqrt(self.T))
        )

    def vega(self) -> float:
        return float(self.S * stats.norm.pdf(self._d1()) * np.sqrt(self.T))

    def theta(self) -> float:
        D1, D2 = self._d1(), self._d2()
        pdf_d1 = stats.norm.pdf(D1)
        discount = self.K * np.exp(-self.r * self.T)
        common = -self.S * pdf_d1 * self.sigma / (2 * np.sqrt(self.T))

        if self.option_type == OptionType.CALL:
            return float(common - self.r * discount * stats.norm.cdf(D2))
        return float(common + self.r * discount * stats.norm.cdf(-D2))

    def rho(self) -> float:
        D2 = self._d2()
        discount_T = self.K * self.T * np.exp(-self.r * self.T)
        if self.option_type == OptionType.CALL:
            return float(discount_T * stats.norm.cdf(D2))
        return float(-discount_T * stats.norm.cdf(-D2))


class AmericanOption(Option):
    """Option américaine : Monte Carlo Longstaff–Schwartz."""

    def __init__(
        self,
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float,
        option_type: OptionType,
        *,
        n_paths: int = 50_000,
        n_steps: int = 252,
        seed: int | None = 42,
    ):
        super().__init__(S, K, T, r, sigma, option_type, ExerciseStyle.AMERICAN)
        self.n_paths = n_paths
        self.n_steps = n_steps
        self.seed = seed

    def with_spot(self, S: float) -> "AmericanOption":
        return AmericanOption(
            S,
            self.K,
            self.T,
            self.r,
            self.sigma,
            self.option_type,
            n_paths=self.n_paths,
            n_steps=self.n_steps,
            seed=self.seed,
        )

    def price(self) -> float:
        from libs.montecarlo import price_american_lsm

        return price_american_lsm(
            self.S,
            self.K,
            self.T,
            self.r,
            self.sigma,
            self.option_type,
            n_paths=self.n_paths,
            n_steps=self.n_steps,
            seed=self.seed,
        )
