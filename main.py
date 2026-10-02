from libs.option import Option, OptionType, ExerciseStyle
import numpy as np


call = Option(S=100, K=100, T=1, r=0.05, sigma=0.2, option_type=OptionType.CALL, exercise_style=ExerciseStyle.EUROPEAN)
put = Option(S=100, K=100, T=1, r=0.05, sigma=0.2, option_type=OptionType.PUT, exercise_style=ExerciseStyle.EUROPEAN)
    


