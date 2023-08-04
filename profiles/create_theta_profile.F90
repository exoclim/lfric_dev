program create_theta_profile

  
  use constants_mod,                 only: i_def, r_def, pi
  use planet_config_mod,             only: p_zero, kappa, rd, gravity, radius, domain_top
  use deep_hot_jupiter_forcings_mod, only: deep_hot_jupiter_equilibrium_theta,             &
                                           deep_hot_jupiter_newton_frequency,              &
                                           night_side_temp, day_side_temp,                 &
                                           deep_hot_jupiter_newton_frequency

  implicit none 
  
  integer(kind=i_def), parameter :: n_fine_points = 1000, n_init_profile = 66
  real(kind=r_def), parameter :: deg_to_rad = pi / 180.0_r_def
  real(kind=r_def), parameter :: p_min = 0.1
  character(len=1), parameter :: comma = ","

  integer(kind=i_def) :: i, j
  real(kind=r_def) :: p_points(n_fine_points), t_day_points(n_fine_points),                &
                      t_night_points(n_fine_points), t_initial_points(n_fine_points),      &
                      theta_initial_points(n_fine_points), r_initial_points(n_fine_points),&
                      freq_initial_points(n_fine_points)
  real(kind=r_def) :: theta(n_init_profile), height(n_init_profile)
  real(kind=r_def) :: log10p_zero, delta_log10p, pressure, exner, integration_coeff
  real(kind=r_def) :: delta_height, r

  log10p_zero = log10(p_zero)
  delta_log10p = log10(p_zero / p_min) / real(n_fine_points - 1)
  do i = 1, n_fine_points
    pressure = 10.0 ** (log10p_zero - real(i - 1) * delta_log10p)
    exner = (pressure / p_zero) ** kappa
    p_points(i) = pressure
    t_day_points(i) = day_side_temp(exner)
    t_night_points(i) = night_side_temp(exner)
    t_initial_points(i) = 0.5_r_def * (t_day_points(i) + t_night_points(i))
    theta_initial_points(i) = t_initial_points(i) / exner
    freq_initial_points(i) = deep_hot_jupiter_newton_frequency(exner)
  end do

  integration_coeff = rd  / (gravity * radius ** 2)
  !integration_coeff = rd / gravity
  r_initial_points(1) = radius
  do i = 2, n_fine_points
    r_initial_points(i) = 1.0_r_def / (integration_coeff                                   &
                          * sqrt(t_initial_points(i) * t_initial_points(i-1))              &
                          * log(p_points(i) / p_points(i - 1))                             & 
                          + 1.0_r_def / r_initial_points(i - 1)                            &                      
                          )
    !r_initial_points(i) = r_initial_points(i - 1) - integration_coeff                       &
    !                      * sqrt(t_initial_points(i) * t_initial_points(i-1))               &
    !                      * log(p_points(i) / p_points(i - 1))
  end do

  open(unit=10, file="profiles.csv", status="unknown")
  write(10,*) "pressure", comma, "day_side_temperature", comma, "night_side_temperature",  &
              comma, "initial_temperature", comma, "initial_potential_temperature", comma, &
              "radius", comma, "radiative_newton_frequency"
  do i = 1, n_fine_points
    write(10,*) p_points(i), comma, t_day_points(i), comma, t_night_points(i), comma,      &
               t_initial_points(i), comma, theta_initial_points(i), comma,                 &
               r_initial_points(i), comma, freq_initial_points(i)
  end do
  close(unit=10)

  delta_height = domain_top / real(n_init_profile)
  do i = 1, n_init_profile
    height(i) = real(i) * delta_height
  end do

  do i = 1, n_init_profile
    r = radius + height(i)
    do j = 1, n_fine_points
      if (r <= r_initial_points(j)) then
        theta(i) = theta_initial_points(j) + (r - r_initial_points(j))                    & 
                   * (theta_initial_points(j - 1) - theta_initial_points(j))              &
                   / (r_initial_points(j - 1) - r_initial_points(j))
        !write(*,*) i, j, r, r_initial_points(j), theta_initial_points(j), height(i), theta(i)
        exit 
      end if
    end do
  end do
    
  open(unit=10, file="theta_vs_r.dat", status="unknown")
  write(10,'(100(ES9.3E2,A1))') (theta(i), comma, i=1, n_init_profile)
  write(10,'(100(ES9.3E2,A1))') (height(i), comma, i=1, n_init_profile)
  close(unit=10)

end program create_theta_profile
