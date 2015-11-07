import math

INITIAL_RATING = 250
K = 50.0 # Rating coefficient (defined by Bonzini USA to be 50)
F = 100.0 # Weight factor

# We = 1/ (10 (-D/F) + 1);
def wining_expectancy(diff_ratings):
    return 1.0 / (math.pow(10.0, -diff_ratings / F) + 1)


# Rn = Ro + K(S-We)
def rating_increment(score_perc, diff_ratings):
    return K * (score_perc - wining_expectancy(diff_ratings))




