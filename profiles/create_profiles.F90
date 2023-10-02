program create_profiles

  use constants_mod,     only: i_def, r_def, pi
  use planet_config_mod, only: p_zero, kappa, rd, cp, radius, domain_top, gravity

  use deep_hot_jupiter_forcings_mod, only: day_side_temp, night_side_temp

  implicit none
  
  integer(kind=i_def), parameter :: n_fine_points = 1000, n_profile = 100
  integer(kind=i_def)            :: i, j, idx

  real(kind=r_def), parameter :: p_min = 0.1
  real(kind=r_def) :: p_pts(n_fine_points), tday_pts(n_fine_points),   &
                      tnight_pts(n_fine_points), t_pts(n_fine_points), &
                      theta_pts(n_fine_points), r_pts(n_fine_points),  &
                      exner_pts(n_fine_points)
  real(kind=r_def) :: r_prof(n_profile), theta_prof(n_profile)
  real(kind=r_def) :: del_logp, logp, logp_min, logp_zero
  real(kind=r_def) :: int_coeff, r_inv, del_r, check

  character(len=1), parameter :: comma = ','

  logp_min = log10(p_min)
  logp_zero = log10(p_zero)
  del_logp = (logp_min - logp_zero) / real(n_fine_points)
  do i = 1, n_fine_points
     logp = logp_zero + real(i-1) * del_logp
     p_pts(i) = 10.0 ** logp
     exner_pts(i) = (p_pts(i) / p_zero) ** kappa
     tday_pts(i) = day_side_temp(exner_pts(i))
     tnight_pts(i) = night_side_temp(exner_pts(i))
     t_pts(i) = (tday_pts(i) + tnight_pts(i)) / 2
     theta_pts(i) = t_pts(i) / exner_pts(i)
  end do

  int_coeff = cp / (gravity * radius **2)
  r_pts(1) = radius
  do i = 2, n_fine_points
    r_inv = 1.0 / r_pts(i-1)                       &
            + int_coeff                            &
            * sqrt (theta_pts(i) * theta_pts(i-1)) &
            * (exner_pts(i) - exner_pts(i-1))
    r_pts(i) = 1.0 / r_inv 
  end do

  open(unit=99, file='profiles.csv', status='unknown')
    write(99, *) 'Pressure', comma,    &
                 'Exner', comma,       &
                 'Temperature', comma, &
                 'Theta', comma,       &
                 'Radius'
    do i = 1, n_fine_points
      write(99,* ) p_pts(i), comma,     &
                   exner_pts(i), comma, &
                   t_pts(i), comma,     &
                   theta_pts(i), comma, &
                   r_pts(i)
    end do  
  close(unit=99)

  del_r = domain_top / real(n_profile - 1)
  do i = 1, n_profile
    r_prof(i) = radius + del_r * real(i - 1)
    do j = 1, n_fine_points - 1
      check = (r_prof(i) - r_pts(j)) * (r_pts(j+1) - r_prof(i))
      if (check >= 0) then
        idx = j
        exit
      end if
    end do  
    theta_prof(i) = theta_pts(idx)                        &
                    + (r_prof(i) - r_pts(idx))            &
                    * (theta_pts(idx) - theta_pts(idx+1)) &
                    / (r_pts(idx) - r_pts(idx+1))
  end do

  open(unit=99, file='theta_vs_r.csv', status='unknown')
    write(99,'(100(ES9.3E2,A1))') (theta_prof(i), comma, i = 1, n_profile)
    write(99,'(100(ES9.3E2,A1))') ((r_prof(i)-radius), comma, i = 1, n_profile) 
  close(unit=99)
     
end program create_profiles
