from libs.option import Option, OptionType
import math


class OptionStrategy:
    def __init__(self, options: list[Option], quantities: list[float] | None = None):
        """
        options    : liste d'options du livre
        quantities : +1 = long, -1 = short (même longueur que options)
                     par défaut tout en long (+1)
        """
        self.options = options
        self.quantities = quantities if quantities is not None else [1.0] * len(options)
        if len(self.quantities) != len(self.options):
            raise ValueError("options et quantities doivent avoir la même longueur")

    def price(self):
        return sum(q * opt.price() for q, opt in zip(self.quantities, self.options))

    def delta(self):
        return sum(q * opt.delta() for q, opt in zip(self.quantities, self.options))

    def gamma(self):
        return sum(q * opt.gamma() for q, opt in zip(self.quantities, self.options))

    def vega(self):
        return sum(q * opt.vega() for q, opt in zip(self.quantities, self.options))

    def theta(self):
        return sum(q * opt.theta() for q, opt in zip(self.quantities, self.options))

    def rho(self):
        return sum(q * opt.rho() for q, opt in zip(self.quantities, self.options))

    @staticmethod
    def _intrinsic(opt: Option, S: float) -> float:
        if opt.option_type == OptionType.CALL:
            return max(S - opt.K, 0.0)
        return max(opt.K - S, 0.0)

    def payoff_at(self, S: float) -> float:
        """
        Payoff brut à l'expiration pour un spot S_T = S.
        Somme signée des intrinsèques uniquement (sans la prime).
        """
        return sum(
            q * self._intrinsic(opt, S)
            for q, opt in zip(self.quantities, self.options)
        )

    def pnl_at_expiry(self, S: float) -> float:
        """
        P&L en valeur terminale à l'expiration :
            P&L_T = payoff_T - V_0 * e^{r T}
        La prime payée en t=0 est capitalisée jusqu'à T (taux de chaque leg).
        """
        total = 0.0
        for q, opt in zip(self.quantities, self.options):
            payoff_T = self._intrinsic(opt, S)
            premium_fwd = opt.price() * math.exp(opt.r * opt.T)
            total += q * (payoff_T - premium_fwd)
        return total
