import datetime

import pandas

import spacepy_field

import gc
gc.set_threshold(10000, 10, 10)


def plot(t, y1, y2, figsize=(8.5, 12), facecolor='white', styles=None):
  from datetick import datetick
  from matplotlib import pyplot as plt

  ylabels = ['$B_x$ (nT)', '$B_y$ (nT)', '$B_z$ (nT)']
  n_stack = y1.shape[1]

  plt.figure(figsize=figsize, facecolor=facecolor)
  gs = plt.gcf().add_gridspec(n_stack)
  axs = gs.subplots(sharex=True)

  for i in range(n_stack):
    axs[i].plot(t, y1[:, i], 'k', label='measured')
    axs[i].set_ylabel(ylabels[i])
    axs[i].grid(True)
    for midx, model in enumerate(y2.keys()):
      axs[i].plot(t, y2[model][:, i], label=model)
    if i == 0:
      axs[i].legend()

  datetick()
  plt.show()


def compute(satellite_df, extMag, n_max=-1):
  print(f"Calculating {extMag} model ...")

  # https://github.com/spacepy/spacepy/blob/main/Doc/source/coordinates.rst:
  #  "... the definitions of an Earth radius differ (SpacePy = 6378.137km; IRBEM = 6371.2 km)"
  R_E = 6371.2

  positions = (satellite_df[['x[km]', 'y[km]', 'z[km]']].values / R_E).tolist()

  times = []
  for idx, row in satellite_df.iterrows():
    time = f"{int(row['year'])}-{int(row['month']):02d}-{int(row['day']):02d}T"
    time += f"{int(row['hour']):02d}:{int(row['minute']):02d}:00"
    times.append(datetime.datetime.strptime(time, "%Y-%m-%dT%H:%M:%S"))

  times = times[:n_max]
  positions = positions[:n_max]

  b_models = {}
  for extMag in extMags:
    print(f"Calculating {extMag} model ...")
    b_models[extMag] = spacepy_field.field(times, positions, extMag, progress=True, grid=False, csys='GSM', intMag=0)

  return times, positions, b_models

def stats(b_meas, b_models):
  pass

n_max = 100
extMags = ['T89', 'T96']

# Table 1 in documentation,
# ../timeseries-predict/data/raw/satellite-b/doc/Magnetic Field Modeling Database Description Final.pdf,
# indicates that position and field in GSM.
satellite_pkl = "../timeseries-predict/data/raw/satellite-b/files/goes9_1996_avg_900_omni.pkl"
satellite_df = pandas.read_pickle(satellite_pkl)

times, positions, b_models = compute(satellite_df, extMags, n_max=n_max)

b_meas = satellite_df[['bx[nT]', 'by[nT]', 'bz[nT]']].values[:n_max]
b_igrf = spacepy_field.field(times, positions, '0', grid=False, csys='GSM', intMag=0)
b_meas_tot = b_meas + b_igrf

#s = stats(b_meas_tot, b_igrf, b_models)
plot(times, b_meas_tot, b_models)