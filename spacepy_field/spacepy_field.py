import logging

import numpy

import spacepy.time as spt
import spacepy.coordinates as spc
import spacepy.irbempy as irbem

from . import install_deps

logger = logging.getLogger(__name__)

def _print(extMag, time, position, Bvec):
  if logger.getEffectiveLevel() < logging.INFO:
    return
  info_str = f"{extMag:10s} {time}"
  info_str += f" x: {position[0]:6.1f} y: {position[1]:6.1f} z: {position[2]:6.1f}"
  info_str += f" Bx: {Bvec[0]:10.2f} By: {Bvec[1]:10.2f} Bz: {Bvec[2]:10.2f}"
  logger.info(info_str)

def field(times, positions, extMags, csys='GSM', options=None):

  # TODO: Get from a query to SpacePy:
  extMags_avail = ['0', 'MEAD', 'T87SHORT', 'T87LONG', 'T89', 'OPQUIET', 'OPDYN', 'T96', 'OSTA', 'T01QUIET', 'T01STORM', 'T05', 'ALEX', 'TS07']

  if isinstance(positions, list) and len(positions) == 3:
    positions = [positions]

  if isinstance(times, str):
    times = [times]

  if isinstance(extMags, str):
    extMags = [extMags]

  for extMag in extMags:
    if extMag not in extMags_avail:
      raise ValueError(f"extMag {extMag} not in {extMags_avail}")
    if extMag in ['T87SHORT', 'T87LONG', 'T89', 'T96', 'T01QUIET', 'T01STORM', 'T05', 'TS07']:
      install_deps.omni()

  # `extMag` is described at https://spacepy.github.io/irbempy.html
  # Possible values are '0', 'MEAD', 'T87SHORT', 'T87LONG', 'T89', 'OPQUIET',
  # 'OPDYN', 'T96', 'OSTA', 'T01QUIET', 'T01STORM', 'T05', 'ALEX', and 'TS07'.

  if options is None:
    options = [0, 0, 0, 0, 1]

    # `options` is described at https://spacepy.github.io/autosummary/spacepy.irbempy.htm
    # The 5th element sets internal magnetic field model, with choices of:
    #   0 = IGRF
    #   1 = Eccentric tilted dipole
    #   2 = Jensen & Cain 1960
    #   3 = GSFC 12/66 updated to 1970
    #   4 = User-defined model (Default: Centred dipole + uniform [Dungey open model] )
    #   5 = Centred dipole

  B = {}
  for time in times:

    t = spt.Ticktock(time, 'ISO')

    if 'TS07' in extMags:
      install_deps.ts07(year=int(time[0:4]), doy=t.DOY[0])

    for position in positions:
      coord = spc.Coords(position, csys, 'car', use_irbem=True)
      for extMag in extMags:
        Bfield = irbem.get_Bfield(t, coord, extMag=extMag)
        Bvec = Bfield["Bvec"][0]
        if extMag not in B:
          B[extMag] = {}
        if time not in B[extMag]:
          B[extMag][time] = []
        B[extMag][time].append(Bvec)
        _print(extMag, time, position, Bvec)
    B[extMag][time] = numpy.array(B[extMag][time])

  if len(extMags) == 1:
    if len(times) == 1:
      if len(positions) == 1:
        return B[extMags[0]][times[0]][0]
      return B[extMags[0]][times[0]]
    return B[extMags[0]]
  return B
