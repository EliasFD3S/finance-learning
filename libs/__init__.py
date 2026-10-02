"""
Namespace public de la lib finance.

Usage :
    import libs as fi
    call = fi.EuropeanOption(...)

    # ou
    from libs import EuropeanOption, OptionType, simulate_heston_paths
"""

from libs.option import (
    AmericanOption,
    EuropeanOption,
    ExerciseStyle,
    Option,
    OptionType,
)
from libs.exotics import (
    AsianAverage,
    AsianOption,
    BarrierOption,
    BarrierType,
    DigitalOption,
    LookbackOption,
    LookbackType,
)
from libs.optionstrategy import OptionStrategy
from libs.montecarlo import (
    discount_mean_payoff,
    price_american_lsm,
    simulate_gbm_paths,
)
from libs.heston import feller_ok, simulate_heston_paths
from libs import plotoption as plot

__all__ = [
    # vanilles
    "Option",
    "EuropeanOption",
    "AmericanOption",
    "OptionType",
    "ExerciseStyle",
    # exotiques
    "AsianOption",
    "AsianAverage",
    "DigitalOption",
    "BarrierOption",
    "BarrierType",
    "LookbackOption",
    "LookbackType",
    # stratégies
    "OptionStrategy",
    # MC / vol
    "simulate_gbm_paths",
    "simulate_heston_paths",
    "price_american_lsm",
    "discount_mean_payoff",
    "feller_ok",
    # plots (sous-module)
    "plot",
]
