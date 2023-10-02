"""
This script generates a theta vs r profile
"""

import argparse
import math

from deep_hot_jupiter import (
    Cp,
    GRAVITY,
    KAPPA,
    P_ZERO,
    RADIUS,
    temperature_from_pressure,
)

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-s",
        "--size",
        help="Number of points in profile",
        type=int,
        default=100,
    )

    args = parser.parse_args()

    number_profile_points = args.size
    delta_p = (0.1 - P_ZERO) / number_profile_points

    int_coeff = Cp / (GRAVITY * RADIUS**2)
    r = RADIUS
    p = P_ZERO
    exner = (p / P_ZERO) ** KAPPA
    theta = temperature_from_pressure(pressure=p) / exner
    print(p, exner, theta, r)

    for _ in range(number_profile_points):

        p_new = p + delta_p
        exner_new = (p_new / P_ZERO) ** KAPPA
        theta_new = temperature_from_pressure(pressure=p_new) / exner_new
        r_new = 1.0 / (
            1.0 / r + int_coeff * math.sqrt(theta * theta_new) * (exner_new - exner)
        )

        p = p_new
        exner = exner_new
        theta = theta_new
        r = r_new
        print(p, exner, theta, r)
