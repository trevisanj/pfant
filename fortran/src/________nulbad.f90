!|||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||
!||| MODULE ||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||
!|||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||
!>
!> Prefixes:
!> @
module nulbad_calc
  use misc_math
  use logging
  use config
  use dimensions
  use reader_main
  implicit none

  public nulbad_calc_

  private

  !^^^^^ PUBLIC  ^^^^^
  !vvvvv PRIVATE vvvvv

  integer, parameter :: MAX_P_IFT = 1501 !< length of "convolution function" (odd number)
  integer, parameter :: IPPTOT = (MAX_P_IFT-1)/2!< "TAILLE MAX DE LA FCT DE CONV"

  ! Gaussian function variables, calculated by cafconvh()
  real*8 :: &
   p_tfi(MAX_P_IFT), &  !< x-axis values of gaussian function (calculated by nulbad::cafconvh())
   p_fi(MAX_P_IFT)      !< y-axis values of gaussian function (calculated by nulbad::cafconvh())
  integer, private :: p_ift !< Number of points of gaussian function (calculated by nulbad::cafconvh())

  ! Variables set by read_spectrum()
  real*8, allocatable :: rs_ffnu(:)
  integer :: rs_ktot


  ! prefix "rs": variables filled by read_spectrum()
  character :: rs_titc*20
  real*8 :: &
   rs_tetaeff, & !< ?doc?
   rs_glog,    & !< ?doc?
   rs_asalog,  & !< ?doc?
   rs_amg,     & !< ?doc?
   rs_l0,      & !< ?doc?
   rs_lf,      & !< ?doc?
   rs_dpas,    & !< ?doc?
   rs_nhe_bid    !< ?doc?

  integer, parameter :: UNIT_=199 !< unit for file I/O

  ! x_* values may come either from command line or dfile:main
  real*8 :: x_fwhm, x_pat
  character*128 :: x_fn_flux, x_fn_cv, x_flprefix
  !> Whether or not the spectrum is normalized.
  !> @sa source for nulbad_init()
  logical x_norm
contains

  !=======================================================================================
  !> Initialization of this module
  !>
  !> One of the tasks if the initialization of the x_* variables, whose values may be
  !> either set from the command line or taken from dfile:main

  subroutine nulbad_init()
    ! MAX_P_IFT must be an odd number
    if (mod(MAX_P_IFT, 2) .eq. 0) then
      call pfant_halt('MAX_P_IFT='//int2str(MAX_P_IFT)//' must be an odd number', &
       is_assertion=.true.)
    end if

    !=====
    ! Assigns x_*
    !=====
    ! values in config_* variables have preference, but if they are uninitialized, will
    ! pick values from dfile:main
    x_fwhm = config_fwhm
    x_pat = config_pat
    x_fn_flux = config_fn_flux
    x_fn_cv = config_fn_cv
    x_norm = config_norm
    if (config_fwhm .eq. -1) then
      call assure_read_main(config_fn_main)
      x_fwhm = main_fwhm
      call parse_aux_log_assignment('x_fwhm', real82str(x_fwhm, 3))
    end if
    if (config_pat .eq. -1) then
      call assure_read_main(config_fn_main)
      x_pat = main_pas
      call parse_aux_log_assignment('x_pat', real82str(x_pat, 3))
    end if
    if (config_flprefix .eq. '?') then
      call assure_read_main(config_fn_main)
      x_flprefix = main_flprefix
      call parse_aux_log_assignment('x_flprefix', x_flprefix)
    else
      x_flprefix = config_flprefix
    end if
    if (config_fn_flux .eq. '?') then
      call assure_read_main(config_fn_main)
      if (x_norm) then
        x_fn_flux = trim(x_flprefix)//'.norm'
      else
        x_fn_flux = trim(x_flprefix)//'.spec'
      end if
      call parse_aux_log_assignment('x_fn_flux', trim(x_fn_flux))
    end if
    if (config_fn_cv .eq. '?') then
      call assure_read_main(config_fn_main)
      x_fn_cv = trim(x_fn_flux)//'.nulbad'
      call parse_aux_log_assignment('x_fn_cv', trim(x_fn_cv))
    end if

    call read_spectrum()
  end

  !=======================================================================================
  !> Reads spectrum file

  subroutine read_spectrum()
    ! variables with suffix "_bid" are read from file, but used for nothing
    real*8 echx_bid, echy_bid, fwhm_bid, lzero_bid, lfin_bid
    integer :: itot, ikeytot, icle, d, k, size_ffnu
    real*8 fnu(MAX_DTOT)  ! temporary, just for reading one "icle" iteration

    open(unit=UNIT_,file=x_fn_flux, status='unknown')

    icle = 1
    rs_ktot = 0

    do while (.true.)
      read(UNIT_, 1130) &
       ikeytot,        & ! used locally
       rs_titc,    & ! written back in output file
       rs_tetaeff, & ! written back
       rs_glog,    & ! written back
       rs_asalog,  & ! written back
       rs_nhe_bid,        & ! read and used in logging only
       rs_amg,     & ! written back
       rs_l0,      & ! used by nulbad_calc() & written back
       rs_lf,      & ! written back
       lzero_bid,      & ! read and discarded
       lfin_bid,       & ! read and discarded
       itot,           & ! used locally
       rs_dpas,    & ! used by nulbad_calc()
       echx_bid,       & ! read and discarded
       echy_bid,       & ! read and discarded
       fwhm_bid          ! read and discarded
      1130 format(i5, a20, 5f15.5, 4f10.1, i10, 4f15.5)

      ! allocates rs_ffnu at first iteration
      if (icle .eq. 1) then
        size_ffnu = ikeytot*itot
        allocate(rs_ffnu(size_ffnu)) ! This is probably a slight overallocation
      end if

      read(UNIT_, *)(fnu(d),d=1,itot)

      ! write(lll,*) ikeytot,itot
      ! call log_debug(lll)

      ! pfant writes redundant data: last value of iteration ikey equals first value of
      ! iteration ikey+1. So the following tweak on itot is to account for this.
      ! In the last iteration, the last point is not discarded.
      if (icle .eq. ikeytot) itot = itot+1
      do d = 1,itot-1
        k=rs_ktot+d
        rs_ffnu(k)=fnu(d)
      end do
      rs_ktot = k

      icle = icle+1
      if(icle .gt. ikeytot) exit
    end do

    ! print *, 'AAAAAAA rs_ktot', rs_ktot,' size_ffnu', size_ffnu

    close(unit=UNIT_)
  end

  !=======================================================================================
  !> Main routine of this module

  subroutine nulbad_calc_()
    real*8, parameter :: C = 2.997929E+10
    integer d, dmj, dtotc, k, i, ip, j, jp1, kktot, m
    real*8, dimension(:), allocatable :: ffl, lambd, alfl, afl, fl, tl
    real*8 alf, alz, ca, cb

    call nulbad_init()

    allocate(ffl(rs_ktot), lambd(rs_ktot), alfl(rs_ktot), afl(rs_ktot), fl(rs_ktot), &
     tl(rs_ktot))


    ! Note: will now replace output file if already existent
    open(unit=UNIT_,status='replace',file=x_fn_cv)

    do k = 1, rs_ktot
      lambd(k) = rs_l0+(k-1)*rs_dpas
    end do


    ! transformation de Fnu en Flambda
    if(config_flam) then
      do k = 1, rs_ktot
        if (.not. x_norm) then
          ca = 1.e+11/(lambd(k)**2)
          !  rs_ffnu(10(-5) etait x 10(5), donc cte=10(11) et pas 10(16)
          cb = ca*c
          ffl(k) = rs_ffnu(k)*cb
        else
          ffl(k) = rs_ffnu(k)
        end if
      end do

      write(lll,122) rs_dpas, rs_ktot
      122  format(2x,'pas=',f8.3,2x,'ktot=', i10)
      call log_debug(lll)
    end if

    ip = int(x_pat/rs_dpas)

    if (ip .lt. 1) then
      call log_warning('New step ('//real82str(x_pat, 3)//&
       ') lower than old step ('//real82str(rs_dpas, 3)//'), ip forced to 1')
      ip = 1
    end if


    !
    !  Convolution sp synthetique avec profil instrumental
    !
    call cafconvh()
    call log_debug('p_ift='//int2str(p_ift))

    j = (p_ift-1)/2
    jp1 = j+1
    dmj = rs_ktot-j
    dtotc = dmj-jp1+1

    m = 0
    do d = jp1,dmj,ip
      m = m+1
      tl(m) = lambd(d)
    end do
    kktot = m

    if(config_flam) then
      do k = 1,rs_ktot
        fl(k) = ffl(k)
      end do
    else
      do k = 1,rs_ktot
        fl(k) = rs_ffnu(k)
      end do
    end if

    call volut() ! calculates alfl

    k=0
    do i = jp1, dmj, ip
      k = k+1
      afl(k) = alfl(i)
    end do
    kktot = k

    alz = tl(1)
    alf = tl(kktot)



    write(UNIT_,201) rs_titc,rs_tetaeff,rs_glog,rs_asalog,rs_amg
    201 format('#',A,'Tef=',F6.3,X,'log g=',F4.1,X,'[M/H]=',F5.2,X,F5.2)

    write(UNIT_,202) kktot,rs_l0,rs_lf,x_pat,x_fwhm
    202 format('#',I6,2X,'0. 0. 1. 1. Lzero =',F10.2,2x,'Lfin =', &
               F10.2,2X,'PAS =',F5.2,2x,'FWHM =',F5.2)

    !write(*,*) 'ppppppppppppp', afl(1), alfl(1)

    do k=1,kktot
      write(UNIT_,*) tl(k), afl(k)
    end do

    close(unit=UNIT_)  ! xxx

    !#loggingx4
    write(lll,110) rs_tetaeff,rs_glog,rs_asalog,rs_nhe_bid,rs_amg
    110 format(2X,'tetaeff=',F8.3,2X,'log g=',F6.2,2X,'[M/H]=',F6.2, &
               2X,'NHE=',F5.2,2X,'[Mg/Fe]=',F6.3)
    call log_info(lll)

    write(lll,130) alz,alf,kktot,x_pat,x_fwhm
    130 format(2X,'Lzero=',F8.3,2x,'Lfin=',F8.2,2x,'KKTOT=',I7, &
               2X,'PAS nouveau =',F5.2,2x,'FWHM=',F5.2)
    call log_info(lll)

    write(lll,120) rs_l0,rs_lf,rs_ktot,rs_dpas
    120 format(2X,'Lzero=',F8.3,2x,'Lfin=',F8.2,2x,'KTOT =',I7, &
               2X,'PAS original='F7.4)
    call log_info(lll)

    write(6,'(12F6.3)') (afl(k),k=1,12)
    call log_info(lll)

    call log_info('File '//trim(x_fn_cv)//' successfully created.')
  contains

    !=======================================================================================
    !> Calculates alfl

    subroutine volut()
      integer i, imj, j2p, k, jjp1, iimj
      do i = 1,rs_ktot
        alfl(i) = 0.
      end do

      imj = rs_ktot-j
      j2p =  2*j +1
      do i = jp1, imj, ip
        do k = 1, j2p
          alfl(i) = alfl(i) + fl(i-j+k-1) * p_fi(k)*rs_dpas
        end do
      end do

      jjp1 = jp1+1
      iimj = imj+1
      do i = 1,jjp1
        alfl(i) = fl(i)
      end do
      do i = iimj,rs_ktot
        alfl(i) = fl(i)
      end do
    end
  end


  !=======================================================================================
  !>  ON CALCULE FI(tfi) la fonction de convolution EN p_ift PTS
  !>
  !> @verbatim
  !> LA FONCTION DE CONVOLUTION PEUT AVOIR MAX_P_IFT PTS
  !> SI L ON CHANGE CE NBRE DE PTS CHANGER AUSSI IPPTOT=750
  !> DANS LES DATA QUELQUES LIGNES PLUS BAS.
  !> (LA MOITIE DU NBRE TOT DE PTS POUR LE CALCUL DES AT)
  !> @endverbatim

  subroutine cafconvh()
    real*8 :: at(-IPPTOT:+IPPTOT)
    real*8 :: sigma, aa, totlarg, z
    integer i, ifd
    character*392 lll
    real*8, parameter :: SQRT_2 = sqrt(2.)


    ! GAUSS: PROFIL GAUSSIEN DE 1/2 LARG AA
    sigma = x_fwhm/2.35482
    aa = SQRT_2*sigma
    totlarg=3.0 * aa

    !#logging x2
    write(lll,119) x_fwhm,sigma,aa
    119  format(1X,'Profil instrumental gaussien; ', &
     'FWHM =',F7.3,' (A); Sigma=',F7.3,' (A); ', &
     '1/2 Largeur AA =',F7.3,' (A)')
    call log_debug(lll)
    write(lll,134) totlarg
    134 format(' Gaussienne calculee jusqu a une distance du centre:', &
     ' 3(SIGMA*1.414)=',F7.3,' S(A)')
    call log_debug(lll)

    at(0)=0
    do i = 1,IPPTOT
      at(i) = x_pat * i
      at(-i) = -at(i)
      if(at(i) .gt. totlarg) go to 40
    end do

    write(lll,133) totlarg
    133  FORMAT(' LE PROFIL GAUSSIEN PAR LEQUEL ON CONVOLE NE PEUT', &
      ' AVOIR PLUS DE 121 PTS (60 DE CHAQUE COTE DU CENTRE); ', &
      ' CETTE GAUSSIENNE EST CALCULEE JUSQU A UNE DISTANCE DE', &
      ' 3 DEMI-LARGEUR DU CENTRE; ', &
      ' SOIT:',F7.3,' ANGSTROM; ', &
      ' ELARGISSEZ LE PAS DU CALCUL')
    call pfant_halt(lll)

    40 continue
    ifd = i-1
    p_ift = 1 + 2*ifd

    if(p_ift .gt. MAX_P_IFT)  then
      write(lll,137) MAX_P_IFT, p_ift
      137  FORMAT(5X,'LA FCTION PAR LAQUELLE VOUS VOULEZ CONVOLER A ', &
       ' PLUS DE ',i4,' PTS (ift=)',i4,': -CHANGEZ LE PAS-. (LE NBRE DE PTS TOTAL ', &
       ' SUR LA FCTION S OBTIENT EN MULTIPLIANT PAR 6 LE NBRE DE PTS SUR LA DEMI LARGEUR')
      call pfant_halt(lll)
    end if

    do i = 1,p_ift
      p_tfi(i) = at(i-ifd-1)
    end do

    z = RPI*aa

    do i = 1,p_ift
      p_fi(i) = exp( -(p_tfi(i)/aa)**2) / z  ! here's gaussian exponential
    end do
! The following code was merged into a single expression above.
!    do i = 1,p_ift
!      p_fi(i) = exp( -(p_tfi(i)/aa)**2)  ! here's gaussian exponential
!    end do
!    do i = 1,p_ift
!      p_fi(i) = p_fi(i) / z
!    end do
  end
end


!|||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||
!||| PROGRAM |||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||
!|||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||
!> programme NULBT=NULBAD_SQ
!>
!>  lecture et convolution sortie fant93
!>
!>  Programme de lecture des flux en binaire, sortant de
!>      Fantomol93 , calculs de 100A en 100A (ou inferieur a 100A)
!>
!> @verbatim
!> Paula, julho de 2003:
!> - modifiquei para nao normalizar o espectro
!> - a opcao config_convol=F nao estava imprimindo o lambda, corrigi
!> P.Coelho, dez 2003
!> - se config_norm = .TRUE. (saida do pfant ja eh normalizada), nao
!>  altera o valor do fluxo
!> @endverbatim

program nulbad
  use config
  use logging
  use welcome
  use nulbad_calc
  implicit none

  execonf_name = 'nulbad'
  call config_init()
  call nulbad_calc_()
end


