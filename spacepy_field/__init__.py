from spacepy_field.spacepy_field import field
from spacepy_field.spacepy_field import external_models
from spacepy_field.spacepy_field import internal_models
from spacepy_field.spacepy_field import internal_model_name
from spacepy_field.spacepy_field import external_model_name

import spacepy
import os
import time as _time
leapsec_file = os.path.join(spacepy.DOT_FLN, 'data', 'tai-utc.dat')
if not os.path.exists(leapsec_file) or (_time.time() - os.path.getmtime(leapsec_file)) > 180 * 86400:
  spacepy.toolbox.update(leapsecs=True)



def print_results(times, positions, extMag, b_model, csys, intMag, b_meas=None):

  import numpy
  numpy.set_printoptions(precision=2)

  if not isinstance(times, list):
    times = [times]
  if not isinstance(positions[0], list):
    positions = [positions]

  intMag_name = internal_model_name(intMag)
  extMag_name = external_model_name(extMag)

  for i, time in enumerate(times):
    for j, position in enumerate(positions):
      print(f"{time} | extMag = {extMag} ({extMag_name}) | intMag = {intMag} ({intMag_name}) | csys = {csys}")
      if b_meas is not None:
        print(f"  x, y, z  = {position}")
        print(f"model:    Bx, By, Bz = {b_model[i, j]}")
        print(f"measured: Bx, By, Bz = {b_meas[i, j]}")
      else:
        print(f"  x, y, z = {position} | Bx, By, Bz = {b_model[i, j]}")


