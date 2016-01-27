import math

INITIAL_RATING = 1000
K = 50.0 # Rating coefficient (defined by Bonzini USA to be 50)
F = 100.0 # Weight factor

# We = 1/ (10 (-D/F) + 1);
def wining_expectancy(diff_ratings):
    return 1.0 / (math.pow(10.0, -diff_ratings / F) + 1)


# Rn = Ro + K(S-We)
def rating_increment(score_perc, diff_ratings):
    return K * (score_perc - wining_expectancy(diff_ratings))


def predicted_score(diff, MAX_SCORE):
    expected = wining_expectancy(diff)
    if expected > 0.5:
        predicted_right_score = int(round(MAX_SCORE * ((1.0-expected) / expected)))
        predicted_left_score = MAX_SCORE
    else:
        predicted_right_score = MAX_SCORE
        predicted_left_score = int(round(MAX_SCORE * (expected / (1.0-expected))))

    return predicted_left_score, predicted_right_score




