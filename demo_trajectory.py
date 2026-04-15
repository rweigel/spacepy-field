import datetime

import numpy
import pandas

import spacepy_field

def plot(t, y, figsize=(8.5, 12), facecolor='white', styles=None):

  from matplotlib import pyplot as plt

  n_stack = 1
  if isinstance(y[0], list):
    n_stack = len(y[0])
  else:
    y = [y]

  plt.figure(figsize=figsize, facecolor=facecolor)
  gs = plt.gcf().add_gridspec(n_stack)
  axs = gs.subplots(sharex=True)

  for i, _y in enumerate(y):
    if isinstance(t[0], list):
      _t = t[i]
    if isinstance(styles, dict):
      _styles = styles
    else:
      _styles = styles[i]

    axs[i].plot(_t, _y, **_styles)
    axs[i].grid(True)
    #datetick()


extMags = ['T89']

# Table 1 in documentation,
# ../timeseries-predict/data/raw/satellite-b/doc/Magnetic Field Modeling Database Description Final.pdf,
# indicates that position and field in GSM.
satellite_pkl = "../timeseries-predict/data/raw/satellite-b/files/goes9_1996_avg_900_omni.pkl"
satellite_df = pandas.read_pickle(satellite_pkl)

# https://github.com/spacepy/spacepy/blob/main/Doc/source/coordinates.rst:
#  "... the definitions of an Earth radius differ (SpacePy = 6378.137km; IRBEM = 6371.2 km)"
R_E = 6371.2

import gc
gc.set_threshold(10000, 10, 10)


b_models = {}
b_meas_tot = numpy.full((len(satellite_df), 3), numpy.nan)
times = []
for idx, row in satellite_df.iterrows():

  x = float(row['x[km]'])/R_E
  y = float(row['y[km]'])/R_E
  z = float(row['z[km]'])/R_E
  position = [x, y, z]

  bx = float(row['bx[nT]'])
  by = float(row['by[nT]'])
  bz = float(row['bz[nT]'])

  time = f"{int(row['year'])}-{int(row['month']):02d}-{int(row['day']):02d}T"
  time += f"{int(row['hour']):02d}:{int(row['minute']):02d}:00"

  times.append(datetime.datetime.strptime(time, '%Y-%m-%dT%H:%M:%S'))

  b_igrf = spacepy_field.field(time, position, '0', csys='GSM', intMag=0)
  b_meas_tot[idx, :] = numpy.array([bx+b_igrf[0, 0, 0], by+b_igrf[0, 0, 1], bz+b_igrf[0, 0, 2]])

  for extMag in extMags:
    if extMag not in b_models:
      b_models[extMag] = numpy.full((len(satellite_df), 3), numpy.nan)
    b_model = spacepy_field.field(time, position, extMag, csys='GSM', intMag=0)
    b_models[extMag][idx, :] = b_model[0, 0, :]

    spacepy_field.print_results(time, position, extMag, b_model, 'GSM', 0, b_meas=numpy.array([b_meas_tot]))

  if idx > 100:
    break

  print(f"{idx+1}/{len(satellite_df)} complete")

import pdb; pdb.set_trace()