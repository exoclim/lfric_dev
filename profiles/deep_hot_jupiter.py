import math

P_LOW = 100.0
P_HIGH = 1.0e6

DAY_T_LOW = 1000.0
DAY_ALPHA = 0.015
DAY_BETA = -120.0

NIGHT_T_LOW = 250.0
NIGHT_ALPHA = 0.10
NIGHT_BETA = 100.0

OMEGA = 2.06e-5
P_ZERO = 2.2e7
Rd = 4593.0
Cp = 14308.4
KAPPA = Rd / Cp
GRAVITY = 9.42
RADIUS = 9.44e7
DOMAIN_TOP = 1.1e7


def temperature_from_pressure(pressure: float):
    """ "
    Calculate the initial DHJ atmospheric temperature (in K) at any level
    given the pressure (in Pa) at that level.

    Parameters
    ----------
    pressure : float
        The pressure (in Pa)

    Returns
    -------
    Float :
        The temperature (in K)
    """

    if pressure >= P_HIGH:
        log_sigma = math.log10(P_HIGH / 1.0e5)
    elif pressure < P_LOW:
        log_sigma = math.log10(P_LOW / 1.0e5)
    else:
        log_sigma = math.log10(pressure / 1.0e5)

    t_day_active = (
        2149.9581
        + 4.1395571 * log_sigma
        - 186.24851 * log_sigma**2
        + 135.52524 * log_sigma**3
        + 106.20433 * log_sigma**4
        - 35.851966 * log_sigma**5
        - 50.022826 * log_sigma**6
        - 18.462489 * log_sigma**7
        - 3.3319965 * log_sigma**8
        - 0.30295925 * log_sigma**9
        - 0.011122316 * log_sigma**10
    )

    if pressure >= P_HIGH:
        t_day = t_day_active + DAY_BETA * (
            1.0 - math.exp(math.log10(P_HIGH / pressure))
        )
    elif pressure < P_LOW:
        t_day = max(
            t_day_active * math.exp(DAY_ALPHA * math.log10(pressure / P_HIGH)),
            DAY_T_LOW,
        )
    else:
        t_day = t_day_active

    t_night_active = (
        1388.2145
        + 267.66586 * log_sigma
        - 215.53357 * log_sigma**2
        + 61.814807 * log_sigma**3
        + 135.68661 * log_sigma**4
        + 2.0149044 * log_sigma**5
        - 40.907246 * log_sigma**6
        - 19.015628 * log_sigma**7
        - 3.8771634 * log_sigma**8
        - 0.38413901 * log_sigma**9
        - 0.015089084 * log_sigma**10
    )

    if pressure >= P_HIGH:
        t_night = t_night_active + NIGHT_BETA * (
            1.0 - math.exp(math.log10(P_HIGH / pressure))
        )
    elif pressure < P_LOW:
        t_night = max(
            t_night_active * math.exp(NIGHT_ALPHA * math.log10(pressure / P_LOW)),
            NIGHT_T_LOW,
        )
    else:
        t_night = t_night_active

    return (t_night + t_day) / 2.0
