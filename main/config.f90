! This file is part of PFANT.
!
! PFANT is free software: you can redistribute it and/or modify
! it under the terms of the GNU General Public License as published by
! the Free Software Foundation, either version 3 of the License, or
! (at your option) any later version.
!
! PFANT is distributed in the hope that it will be useful,
! but WITHOUT ANY WARRANTY; without even the implied warranty of
! MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
! GNU General Public License for more details.
!
! You should have received a copy of the GNU General Public License
! along with PFANT.  If not, see <http://www.gnu.org/licenses/>.

!> @ingroup gr_config
!> Command-line parsing and respective global variable declarations
!> - Configuration globals with their default values
!> - Routines to parse command-line arguments
!> - All globals have prefix "config_"

module config
  use logging

  integer, parameter :: num_mol=21  ! Number of molecules configured in the program.
                                    ! Conceptually, this should be defined in molecula.f, but there would be cyclic USEs

  !> Logging level (from @ref logging module).
  !>
  !> Possible values: logging::logging_halt, logging::logging_critical, logging::logging_error,
  !> logging::logging_warning, logging::logging_info (default), logging::logging_debug
  integer :: config_loglevel = logging_info

  !=====
  ! File names

  character*256 config_fn_dissoc


  !=====
  ! Variables related to molecules
  !=====

  ! These are configurable

  !> Number of molecules switched off (excluded from calculations)
  integer :: config_num_mol_off = 0
  !> List of molecule ids that are be switched off. Complement of config_molids_on.
  integer :: config_molids_off (num_mol)

  ! These are filled by make_molids()

  !> List of molecule ids that are switched on. Complement of config_molids_off.
  integer, dimension(num_mol) :: config_molids_on
  !> This is actually <code> = num_mol-config_num_mol_off </code>
  integer config_num_mol_on


  !=====
  ! Misc
  !=====

  !> Interpolation type of turbul_VT
  !> @li 1: (default) linear
  !> @li 2: parabolic
  integer :: config_interp = 1


  !> Selector for subroutines FLIN1() and FLINH():
  !> @li 0: (default) integration using 6/7 points depending on main_PTDISK;
  !> @li 1: 26-point integration
  integer :: config_kik = 0



  !=====
  ! Private variables
  !=====

  logical, private :: flag_setup = .false.

  private str2int

contains


  !================================================================================================================================
  !> Does various setup operations.
  !>
  !>   - sets up configuration defaults,
  !>   - parses command-line arguments, and
  !>   - does other necessary operations.
  !>
  !> Must be called at system startup

  subroutine config_setup()
    use logging
    implicit none

    ! Parses command line
    call parseargs()

    ! Configures modules
    logging_level = config_loglevel  ! sets logging level at logging module based on config variable


    call make_molids()

    flag_setup = .true.
  end



  !================================================================================================================================
  !> Returns molecule id given index
  !>
  !> Molecule id is a number from 1 to num_mol, which is uniquely related to a chemical molecule within pfant.

  function get_molid(i_mol)
    implicit none
    integer i_mol, get_molid
    character*80 s  !__logging__

    !--assertion--!
    if (.not. flag_setup) call pfant_halt('get_molid(): forgot to call config_setup()')

    !__spill check__
    if (i_mol .gt. config_num_mol_on) then
      write (s, *) 'get_molid(): invalid molecule index i_mol (', &
       i_mol, ') must be maximum ', config_num_mol_on
      call pfant_halt(s)
    end if

    get_molid = config_molids_on(i_mol)
    return
  end

  !================================================================================================================================
  !> Returns .TRUE. or .FALSE. depending on whether molecule represented by molid is "on" or "off"

  function molecule_is_on(molid)
    implicit none
    integer molid, j
    logical molecule_is_on

    !--assertion--!
    if (.not. flag_setup) &
     call pfant_halt('molecule_is_on(): forgot to call config_setup()')

    molecule_is_on = .true.
    do j = 1, config_num_mol_off
      if (molid .eq. config_molids_off(j)) then
        molecule_is_on = .false.
        exit
      end if
    end do
  end


  !================================================================================================================================
  !> Fills config_molids_on and config_num_mol_on

  subroutine make_molids()
    implicit none
    integer i_mol, j, molid
    logical is_off

    i_mol = 0
    do molid = 1, num_mol
      is_off = .false.  ! Whether molecule I_MOL is off
      do j = 1, config_num_mol_off
        if (molid .eq. config_molids_off(j)) then
          is_off = .true.
          exit
        end if
      end do
      if (.not. is_off) then
        i_mol = i_mol+1
        config_molids_on(i_mol) = molid
      end if
    end do
    config_num_mol_on = i_mol
  end subroutine


  !================================================================================================================================
  !> Parses and validates all command-line arguments.
  !>

  subroutine parseargs()
    use options2
    use logging
    implicit none
    integer k  !> @todo for debugging, take it out
    integer o_len, o_stat, o_remain, o_offset, o_index, iTemp
    character*500 o_arg
    character*128 lll
    logical err_out
    type(option) options(3), opt

    options(1) = option('loglevel', 'l', .TRUE., 'Logging level (1: debug; 2: info; 3: '//&
     'warning; 4: error; 5: critical; 6: halt)', 'level')
    options(2) = option('interp', 'i', .TRUE., 'Interpolation type for subroutine '//&
     'TURBUL() (1: linear; 2: parabolic)', 'type')
    options(3) = option('kik', 'i', .TRUE., 'Selector for subroutines FLIN1() and '//&
     'FLINH() (0 (default): integration using 6/7 points depending on main_PTDISK; '//&
     '1: 26-point integration)', 'type')

    err_out = .FALSE.

    do while (.TRUE.)
      call getopt(options, o_index, o_arg, o_len, o_stat, o_offset, o_remain)

      write(*,*) 'o_index = ', o_index
      write(*,*) 'o_arg = ', o_arg
      write(*,*) 'o_len = ', o_len
      write(*,*) 'o_stat = ', o_stat
      write(*,*) 'o_offset = ', o_offset
      write(*,*) 'o_remain = ', o_remain
      write(*,*) '---------------------------'

      select case(o_stat)
        case (1,2,3)  ! parsing stopped (no error)
           exit
        case (0)  ! option successfully parsed
          opt = options(o_index)

          ! "Uses" config options: validates and assigns to proper config_* variables.
          select case(opt%name)  ! It is more legible select by option name than by index
            case ('loglevel')
              iTemp = parseint(opt, o_arg)
              select case (iTemp)
                case (10, 20, 30, 40, 50, 60)
                  config_loglevel = iTemp*10
                  write(*,*) 'setting logging level to ', config_loglevel
                case default
                  err_out = .TRUE.
              end select

            case ('interp')
              iTemp = parseint(opt, o_arg)
              select case (iTemp)
                case (1, 2)
                  config_INTERP = iTemp
                  write(*,*) 'setting config_interp to ', config_interp
                case default
                  err_out = .TRUE.
              end select

            case ('kik')
              iTemp = parseint(opt, o_arg)
              select case(iTemp)
                case (0, 1)
                  config_KIK = iTemp
                case default
                  err_out = .TRUE.
              end select
          end select

          if (err_out) then
            write (lll, *) 'Argument out of range for option ', get_option_name(opt)
            call PFANT_HALT(lll)
          end if

      end select

      k = k+1
      if (k == 20) then
        stop 'sort this shit'
      end if
    end do
  end subroutine parseargs


END MODULE
