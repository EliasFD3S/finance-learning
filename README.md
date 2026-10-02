# Finance : lib de pricing d’options

Bibliothèque Python pédagogique pour pricer des options **européennes**, **américaines** et **exotiques**, les combiner en stratégies, et tracer payoffs / grecques.

## Installation

Depuis la racine du projet (`finance/`) :

```bash
pip install numpy scipy matplotlib
```

Les imports partent de la racine :

```python
from libs.option import EuropeanOption, OptionType
```

## Architecture

```
finance/
└── libs/
    ├── option.py           # modèle de domaine + vanilles
    ├── exotics.py          # options path-dependent
    ├── montecarlo.py       # simulation GBM + pricers MC
    ├── optionstrategy.py   # agrégation multi-legs
    └── plotoption.py       # visualisation (séparée du pricing)
```

### Rôles des modules

| Module | Responsabilité |
|--------|----------------|
| `option` | Classes `Option` (ABC), `EuropeanOption`, `AmericanOption` ; enums `OptionType`, `ExerciseStyle` |
| `exotics` | `AsianOption`, `DigitalOption`, `BarrierOption`, `LookbackOption` |
| `montecarlo` | `simulate_gbm_paths`, `price_american_lsm`, helpers d’actualisation |
| `optionstrategy` | `OptionStrategy` : somme signée des prix / grecques |
| `plotoption` | Fonctions de plot ; ne contient **pas** de logique de pricing |

### Hiérarchie (polymorphisme)

```
Option (ABC)
├── EuropeanOption     → Black–Scholes (+ grecques analytiques)
├── AmericanOption     → Monte Carlo Longstaff–Schwartz
├── AsianOption        → MC sur la moyenne du chemin
├── DigitalOption      → MC cash-or-nothing
├── BarrierOption      → MC knock-in / knock-out
└── LookbackOption     → MC fixed / floating strike
```

Tout pricing passe par `price()`. Une stratégie manipule des `Option` sans connaître le type concret.

Deux axes distincts :

- **`ExerciseStyle`** : *quand* on peut exercer (`EUROPEAN` / `AMERICAN`)
- **Classe d’exotique** : *quel* payoff path-dependent (+ enums dédiés : `AsianAverage`, `BarrierType`, `LookbackType`)

### Flux typique

```
paramètres (S, K, T, r, σ)
        │
        ▼
   Option concrète  ──price()──►  BS  ou  MC (chemins GBM)
        │
        ▼
  OptionStrategy (quantités ±1)
        │
        ▼
  plotoption (payoff / grecques)
```

## Paramètres communs

| Nom | Sens | Unité |
|-----|------|--------|
| `S` | spot | devise |
| `K` | strike | devise |
| `T` | maturité | **années** (30 j ≈ `30/365`) |
| `r` | taux sans risque (continu) | décimal (`0.05` = 5 %) |
| `sigma` | volatilité | décimal (`0.20` = 20 %) |
| `option_type` | `OptionType.CALL` ou `PUT` | — |

Monte Carlo (kwargs optionnels) : `n_paths`, `n_steps`, `seed`.

## Utilisation

### Européenne (Black–Scholes)

```python
from libs.option import EuropeanOption, OptionType

call = EuropeanOption(S=100, K=100, T=1, r=0.05, sigma=0.2, option_type=OptionType.CALL)
put = EuropeanOption(100, 100, 1, 0.05, 0.2, OptionType.PUT)

call.price()
call.delta()   # grecques analytiques
call.gamma()
call.vega()    # ∂V/∂σ (diviser par 100 pour 1 point de vol)
call.theta()   # annualisé (≈ /365 pour un jour)
call.rho()
call.payoff()  # intrinsèque au spot actuel

# parité call-put (sans dividende) :
# call.price() - put.price()  ≈  S - K * exp(-r*T)
```

### Américaine

```python
from libs.option import AmericanOption, OptionType

am_put = AmericanOption(
    100, 100, 1, 0.05, 0.2, OptionType.PUT,
    n_paths=50_000, n_steps=252, seed=42,
)
am_put.price()  # ≥ put européen (exercice anticipé)
# pas de grecques BS : NotImplementedError (bumps MC possibles)
```

### Exotiques

```python
from libs.option import OptionType
from libs.exotics import (
    AsianOption, AsianAverage,
    DigitalOption,
    BarrierOption, BarrierType,
    LookbackOption, LookbackType,
)

asian = AsianOption(
    100, 100, 1, 0.05, 0.2, OptionType.CALL,
    average=AsianAverage.ARITHMETIC,  # ou GEOMETRIC
    n_paths=50_000,
)

digital = DigitalOption(100, 100, 1, 0.05, 0.2, OptionType.CALL, cash=1.0)

barrier = BarrierOption(
    100, 100, 1, 0.05, 0.2, OptionType.CALL,
    barrier=120.0, barrier_type=BarrierType.UP_AND_OUT,
)

lookback = LookbackOption(
    100, 100, 1, 0.05, 0.2, OptionType.CALL,
    lookback=LookbackType.FIXED_STRIKE,  # ou FLOATING_STRIKE
)
```

Ordres de grandeur utiles :
- asian < vanilla (moyenne moins volatile)
- knock-out < vanilla ; lookback > vanilla
- put américain ≥ put européen

### Stratégies

```python
from libs.optionstrategy import OptionStrategy

# quantities : +1 = long, -1 = short
straddle = OptionStrategy([call, put], quantities=[1, 1])
bull_call = OptionStrategy([call_low_K, call_high_K], quantities=[1, -1])

straddle.price()
straddle.delta()
straddle.payoff_at(S=110)  # P&L à l’expiration pour un spot donné
```

### Graphiques

Les plots sont **hors** des classes d’options :

```python
import libs.plotoption as plot

plot.plot_payoff(call)
plot.plot_price(call)
plot.plot_delta(call)
plot.plot_gamma(call)
plot.plot_vega(call)
plot.plot_theta(call)
plot.plot_rho(call)
plot.plot_strategy_payoff(straddle)
```

`with_spot(S)` (sur chaque `Option`) clone le contrat à un autre spot — utilisé en interne par les plots de grecques.

## Modèles sous-jacents

| Produit | Moteur | Hypothèses |
|---------|--------|------------|
| Européenne | formule BS | GBM, pas de dividende |
| Américaine | Longstaff–Schwartz | GBM, régression sur base `{1, S, S²}` |
| Path-dependent | MC | chemins GBM, payoff actualisé `e^{-rT}` |

Simulation partagée : `libs.montecarlo.simulate_gbm_paths(...)`.

## Étendre la lib

1. Créer une sous-classe de `Option`
2. Implémenter `price()` et `with_spot()`
3. Passer le bon `ExerciseStyle` au `super().__init__`
4. (Optionnel) surcharger les grecques, sinon elles restent `NotImplementedError`
5. Brancher dans une `OptionStrategy` comme n’importe quelle autre `Option`

## Licence

Projet d’apprentissage — usage libre.
