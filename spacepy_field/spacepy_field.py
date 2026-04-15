import numpy

import spacepy.time as spt
import spacepy.coordinates as spc
import spacepy.irbempy as irbem

from . import install_deps


def external_models():
  # TODO: Get from a query to SpacePy. (How?)
  return ['0', 'ALEX', 'MEAD', 'T87SHORT', 'T87LONG', 'T89', 'OPQUIET', 'OPDYN', 'T96', 'OSTA', 'T01QUIET', 'T01STORM', 'T05', 'TS07']


def external_model_name(extMag):
  models = {
    '0': 'IGRF',
    'ALEX': 'Alexeev 2000',
    'MEAD': 'Mead 1964',
    'T87SHORT': 'Tsyganenko 1987 short',
    'T87LONG': 'Tsyganenko 1987 long',
    'T89': 'Tsyganenko 1989',
    'OPQUIET': 'OP77 quiet',
    'OPDYN': 'OP77 dynamic',
    'T96': 'Tsyganenko 1996',
    'OSTA': 'Olsen & Stadsnes 2002',
    'T01QUIET': 'Tsyganenko 2001 quiet',
    'T01STORM': 'Tsyganenko 2001 storm',
    'T05': 'Tsyganenko 2005',
    'TS07': "Tsyganenko & Sitnov 2007"
  }

  if extMag not in models:
    raise ValueError(f"extMag {extMag} not in {list(models.keys())}")
  return models[extMag]


def internal_models():
  return [0, 1, 2, 3, 4, 5]


def internal_model_name(intMag):
  models = {
    0: 'IGRF',
    1: 'Eccentric tilted dipole',
    2: 'Jensen & Cain 1960',
    3: 'GSFC 12/66 updated to 1970',
    4: 'User-defined model (Default: Centred dipole + uniform [Dungey open model] )',
    5: 'Centred dipole'
  }
  if intMag not in models:
    raise ValueError(f"internal {intMag} not in [0, 1, 2, 3, 4, 5]")
  return models.get(intMag, 'Unknown')


def field(times, positions, extMag, csys='GSM', intMag=0):
  """
  Given a time or list of times, position(s), and external magnetic field model,
  return the magnetic field vector(s) in GSM coordinates.

  Is a wrapper for get_Bfield in
  https://github.com/spacepy/spacepy/blob/main/spacepy/irbempy/__init__.py

  Usage:
    b = field(time, position, extMag, csys='GSM', internal=None)

  where 

  `time` is a string or list of strings in ISO format, e.g. '1995-01-02T12:00:00'.

  `position` is a list of 3 floats or a list of lists of 3 floats, in units of
  Earth radii, in the coordinate system specified by `csys`.

  `csys` is the coordinate system of the input position and output B, with
  possible values given in
  https://github.com/spacepy/spacepy/blob/main/spacepy/ctrans/__init__.py

  `extMag` is described at https://spacepy.github.io/irbempy.html
  Possible values are '0' (IGRF), 'MEAD', 'T87SHORT', 'T87LONG', 'T89', 'OPQUIET',
  'OPDYN', 'T96', 'OSTA', 'T01QUIET', 'T01STORM', 'T05', 'ALEX', and 'TS07'.

  `internal` is in integer that corresponds to the internal magnetic field model,
  with choices of:
    0 = IGRF (default)
    1 = Eccentric tilted dipole
    2 = Jensen & Cain 1960
    3 = GSFC 12/66 updated to 1970
    4 = User-defined model (Default: Centred dipole + uniform [Dungey open model] )
    5 = Centred dipole
  """

  # TODO: Get from a query to SpacePy:
  extMags_avail = external_models()

  if extMag not in extMags_avail:
    raise ValueError(f"extMag {extMag} not in {extMags_avail}")
  if extMag in ['T87SHORT', 'T87LONG', 'T89', 'T96', 'T01QUIET', 'T01STORM', 'T05', 'TS07']:
    install_deps.omni()


  if intMag not in [0, 1, 2, 3, 4, 5]:
    raise ValueError(f"internal {intMag} not in [0, 1, 2, 3, 4, 5]")

  options = [0, 0, 0, 0, intMag]

  if isinstance(positions, list) and len(positions) == 3:
    positions = [positions]

  if isinstance(times, str):
    times = [times]


  B = numpy.full((len(times), len(positions), 3), numpy.nan)

  # Note that there is an unused GET_FIELD_MULTI in onera_desp.lib.f that
  # does the looping over time in Fortran. In get_Bfield, the loop is done
  # in Python. So we do the loop here instead of in get_Bfield to be explicit
  # about the time and position handling and due to the fact that we need to
  # anyway for TS07.
  for i, time in enumerate(times):

    t = spt.Ticktock(time, 'ISO')

    if extMag == 'TS07':
      install_deps.ts07(year=int(time[0:4]), doy=t.DOY[0])

    for j, position in enumerate(positions):
      coord = spc.Coords(position, csys, 'car', use_irbem=True)
      Bfield = irbem.get_Bfield(t, coord, extMag=extMag, options=options)
      BGEO = Bfield["Bvec"][0]
      if csys == 'GEO':
        B[i, j] = BGEO
      else:
        B[i, j] = _transform_Bfield(BGEO, time, csys)

  return B


def _transform_Bfield(BGEO, time, csys_xyz):
  cvals = spc.Coords(BGEO, 'GEO', 'car', use_irbem=True)
  cvals.ticks = spt.Ticktock(time, 'ISO')
  return cvals.convert(csys_xyz, 'car').data

