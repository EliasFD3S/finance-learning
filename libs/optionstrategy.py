from libs.option import Option, OptionType


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

    def payoff_at(self, S: float) -> float:
        """Payoff net à l'expiration pour un spot S (intrinsic - prime, signé)."""
        total = 0.0
        for q, opt in zip(self.quantities, self.options):
            if opt.option_type == OptionType.CALL:
                intrinsic = max(S - opt.K, 0.0)
            else:
                intrinsic = max(opt.K - S, 0.0)
            total += q * (intrinsic - opt.price())
        return total
