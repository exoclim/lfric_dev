module constants_mod

  use, intrinsic :: iso_fortran_env, only : int32, real64

  integer, parameter :: i_def = int32
  integer, parameter :: r_def = real64
 
  real(kind=r_def), parameter :: pi  = 4.0_r_def*atan(1.0_r_def)      

end module constants_mod
