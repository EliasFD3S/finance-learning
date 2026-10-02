import libs as fi

S=100
K=100
T=1
r=0.05
sigma=0.2

option1 = fi.EuropeanOption(S=S, K=K, T=T, r=r, sigma=sigma, option_type=fi.OptionType.CALL)
option2 = fi.EuropeanOption(S=S, K=K, T=T, r=r, sigma=sigma, option_type=fi.OptionType.PUT)

strategy = fi.OptionStrategy(options=[option1, option2], quantities=[10, 2])

print(strategy.price())
print(strategy.delta())
print(strategy.gamma())
print(strategy.vega())
print(strategy.theta())
print(strategy.rho())

fi.plot.plot_strategy_payoff(strategy)
