# Finance — lib de pricing d’options

Bibliothèque Python pédagogique pour pricer des options **européennes**, **américaines** et **exotiques**, les combiner en stratégies, simuler des modèles de vol (GBM, Heston), et tracer payoffs / P&L / grecques.

## Installation

Depuis la racine du projet :

```bash
pip install numpy scipy matplotlib
```

Tout s’importe depuis le package `libs` (namespace public).

## Démarrage rapide

```python
import libs as fi

call = fi.EuropeanOption(100, 100, 1, 0.05, 0.2, fi.OptionType.CALL)
put = fi.EuropeanOption(100, 100, 1, 0.05, 0.2, fi.OptionType.PUT)

print(call.price(), call.delta())

straddle = fi.OptionStrategy([call, put], quantities=[1, 1])
print(straddle.price())
print(straddle.payoff_at(110))      # payoff brut
print(straddle.pnl_at_expiry(110))  # P&L en valeur terminale

fi.plot.plot_pnl_at_expiry(call)
```

Équivalent :

```python
from libs import EuropeanOption, OptionType, OptionStrategy
```

---

## Architecture

```
finance/
├── libs/
│   ├── __init__.py         # API publique (namespace)
│   ├── option.py           # Option (ABC), European, American
│   ├── exotics.py          # Asian, Digital, Barrier, Lookback
│   ├── optionstrategy.py   # multi-legs
│   ├── montecarlo.py       # GBM + Longstaff–Schwartz
│   ├── heston.py           # simulation Heston
│   └── plotoption.py       # visualisation
└── README.md
```

### Namespace

`libs/__init__.py` réexporte l’API. Les modules internes restent séparés ; le client n’a en principe besoin que de `import libs as fi`.

| Sous-module | Rôle |
|-------------|------|
| `option` | domaine + vanilles BS / américain |
| `exotics` | path-dependent (MC) |
| `optionstrategy` | agrégation signée |
| `montecarlo` | chemins GBM, pricing américain |
| `heston` | chemins Heston |
| `plotoption` | plots (exposé via `fi.plot`) |

### Hiérarchie

```
Option (ABC)
├── EuropeanOption     → Black–Scholes (+ grecques)
├── AmericanOption     → MC Longstaff–Schwartz
├── AsianOption        → MC moyenne du chemin
├── DigitalOption      → MC cash-or-nothing
├── BarrierOption      → MC knock-in / knock-out
└── LookbackOption     → MC fixed / floating strike
```

- **`ExerciseStyle`** : *quand* on exerce (`EUROPEAN` / `AMERICAN`)
- **Classe d’exotique** : *quel* payoff (+ enums `AsianAverage`, `BarrierType`, `LookbackType`)

Tout pricing passe par `price()`. Une `OptionStrategy` manipule des `Option` sans connaître le type concret.

### Flux

```
paramètres (S, K, T, r, σ [, params Heston])
        │
        ▼
   Option concrète ──price()──► BS  ou  MC (GBM / Heston)
        │
        ▼
  OptionStrategy (quantités ±1)
        │
        ▼
  fi.plot.*  (payoff / P&L / grecques)
```

---

## Paramètres

| Nom | Sens | Unité |
|-----|------|--------|
| `S` | spot | devise |
| `K` | strike | devise |
| `T` | maturité | **années** |
| `r` | taux sans risque (continu) | décimal |
| `sigma` | vol (BS / GBM) | décimal |
| `option_type` | `CALL` / `PUT` | — |

MC : `n_paths`, `n_steps`, `seed`.

---

## Utilisation

### Européenne

```python
import libs as fi

call = fi.EuropeanOption(100, 100, 1, 0.05, 0.2, fi.OptionType.CALL)
call.price()
call.delta(); call.gamma(); call.vega(); call.theta(); call.rho()
call.payoff()       # intrinsèque au spot courant
call.with_spot(110) # clone à un autre spot
```

Cas limites :
- `T <= 0` → intrinsèque
- `σ = 0`, `T > 0` → \(\max(S - K e^{-rT}, 0)\) (call)

### Américaine

```python
put = fi.AmericanOption(100, 100, 1, 0.05, 0.2, fi.OptionType.PUT, n_paths=50_000)
put.price()  # ≥ put européen
```

### Exotiques

```python
asia = fi.AsianOption(
    100, 100, 1, 0.05, 0.2, fi.OptionType.CALL,
    average=fi.AsianAverage.ARITHMETIC, n_paths=50_000,
)
digital = fi.DigitalOption(100, 100, 1, 0.05, 0.2, fi.OptionType.CALL, cash=1.0)
barrier = fi.BarrierOption(
    100, 100, 1, 0.05, 0.2, fi.OptionType.CALL,
    barrier=120, barrier_type=fi.BarrierType.UP_AND_OUT,
)
lookback = fi.LookbackOption(
    100, 100, 1, 0.05, 0.2, fi.OptionType.CALL,
    lookback=fi.LookbackType.FIXED_STRIKE,
)
```

### Stratégies — payoff vs P&L

```python
straddle = fi.OptionStrategy([call, put], quantities=[1, 1])  # +1 long, -1 short

straddle.price()
straddle.delta()

# Payoff brut à T (intrinsèques signées seulement)
straddle.payoff_at(110)

# P&L en valeur terminale : payoff_T − V_0 · e^{rT}
straddle.pnl_at_expiry(110)
```

Ne pas confondre les deux : le payoff ignore la prime ; le P&L capitalise la prime jusqu’à \(T\).

### Simulation

```python
# Black–Scholes / GBM
paths = fi.simulate_gbm_paths(100, 1.0, 0.05, 0.2, n_paths=10_000)

# Heston (Euler + réflexion) — shape (n_paths, n_steps+1)
S, v = fi.simulate_heston_paths(
    S0=100, v0=0.04, r=0.05,
    kappa=2.0, theta=0.04, xi=0.3, rho=-0.7,
    T=1.0, n_paths=10_000, n_steps=252, seed=42,
)
fi.feller_ok(2.0, 0.04, 0.3)  # 2κθ > ξ² ?
```

### Graphiques

```python
fi.plot.plot_payoff(call)              # payoff brut
fi.plot.plot_pnl_at_expiry(call)       # P&L valeur T
fi.plot.plot_delta(call)
fi.plot.plot_strategy_payoff(straddle)
fi.plot.plot_strategy_pnl_at_expiry(straddle)
```

---

## Modèles

| Produit | Moteur | Notes |
|---------|--------|--------|
| Européenne | Black–Scholes | GBM, pas de dividende |
| Américaine | Longstaff–Schwartz | exercice anticipé |
| Path-dependent | MC GBM | payoff actualisé \(e^{-rT}\) |
| Heston | Euler–Maruyama | vol stochastique, biais près de 0 |

---

## Étendre la lib

1. Sous-classer `Option`
2. Implémenter `price()` et `with_spot()`
3. Réexporter dans `libs/__init__.py` (+ `__all__`)

---

## Licence

Projet d’apprentissage — usage libre.
