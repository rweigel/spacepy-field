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

n_max = 100

positions = (satellite_df[['x[km]', 'y[km]', 'z[km]']].values / R_E).tolist()

times = []
for idx, row in satellite_df.iterrows():
  time = f"{int(row['year'])}-{int(row['month']):02d}-{int(row['day']):02d}T"
  time += f"{int(row['hour']):02d}:{int(row['minute']):02d}:00"
  times.append(time)

times = times[:n_max]
positions = positions[:n_max]

b_igrf = spacepy_field.field(times, positions, '0', grid=False, csys='GSM', intMag=0)
b_meas = satellite_df[['bx[nT]', 'by[nT]', 'bz[nT]']].values[:n_max]
b_meas_tot = b_meas + b_igrf


b_models = {}
for extMag in extMags:
  b_models[extMag] = spacepy_field.field(times, positions, extMag, progress=True, grid=False, csys='GSM', intMag=0)

import pdb; pdb.set_trace()