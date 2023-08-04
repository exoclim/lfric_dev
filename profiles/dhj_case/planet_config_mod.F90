module planet_config_mod

  use constants_mod, only: r_def

  real(kind=r_def), parameter :: omega = 2.06E-5
  real(kind=r_def), parameter :: p_zero = 2.2E7
  real(kind=r_def), parameter :: rd = 4593.0
  real(kind=r_def), parameter :: cp = 14308.4
  real(kind=r_def), parameter :: kappa = rd / cp
  real(kind=r_def), parameter :: gravity = 9.42
  real(kind=r_def), parameter :: radius = 9.44E7
  real(kind=r_def), parameter :: domain_top = 1.1E7

end module planet_config_mod
