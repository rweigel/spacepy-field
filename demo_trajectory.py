import os
import datetime

import pandas

import spacepy_field

import gc
gc.set_threshold(10000, 10, 10)


def insert_nan(times, matrix, max_gap):
  """Insert NaN values in matrix where time gaps in times are greater than max_gap."""
  import numpy
  arr = []
  for i in range(len(times)-1):
    arr.append(matrix[i])
    if times[i+1] - times[i] > max_gap:
      arr.append(numpy.full(matrix.shape[1], numpy.nan))
  arr.append(matrix[-1])

  return arr


def plot(b_dict, title="", figsize=(8.5, 12), facecolor='white', styles=None):
  from datetick import datetick
  from matplotlib import pyplot as plt

  t = b_dict['times']
  y1 = b_dict['b_meas']
  y2 = b_dict['b_models']

  ylabels = ['$B_x$ (nT)', '$B_y$ (nT)', '$B_z$ (nT)']
  n_stack = y1.shape[1]

  plt.figure(figsize=figsize, facecolor=facecolor)
  gs = plt.gcf().add_gridspec(n_stack)
  axs = gs.subplots(sharex=True)

  for i in range(n_stack):
    if i == 0:
      axs[i].set_title(title)
    axs[i].plot(t, y1[:, i], 'k', label='measured')
    axs[i].set_ylabel(ylabels[i])
    axs[i].grid(True)
    for midx, model in enumerate(y2.keys()):
      stats = b_dict['metrics'][model]
      label = f"{model} (nans={stats['n_nans'][i]}, PE={stats['pe'][i]:.2f})"
      axs[i].plot(t, y2[model][:, i], label=label)
      axs[i].legend()

  datetick()


def savefig(pkl_dir, pkl):
  from matplotlib import pyplot as plt
  basename = os.path.splitext(os.path.basename(pkl))[0]
  file = os.path.join(pkl_dir, f"{basename}.calc.png")
  print(f"  Saving {file}")
  plt.savefig(file, dpi=300, bbox_inches='tight')


def compute(satellite_df, extMag, n_max=-1):

  # Table 1 in documentation,
  # {pkl_dir}/../doc/Magnetic Field Modeling Database Description Final.pdf,
  # indicates that position and field in GSM.

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
    print(f"  Calculating {extMag} model")
    b_models[extMag] = spacepy_field.field(times, positions, extMag, progress=True, grid=False, csys='GSM', intMag=0)

  return times, positions, b_models


def metrics(b_meas, b_models):
  import numpy
  stats = {}
  for model in b_models.keys():
    n_nan = numpy.sum(numpy.isnan(b_models[model]), axis=0)
    stats[model] = {
      'n_nans': n_nan,
      'mean_error': numpy.nanmean(b_meas - b_models[model], axis=0),
      'mean_abs_error': numpy.nanmean(numpy.abs(b_meas - b_models[model]), axis=0),
      'rmse': numpy.sqrt(numpy.nanmean((b_meas - b_models[model])**2, axis=0)),
      'pe': 1-numpy.nansum((b_meas - b_models[model])**2, axis=0) / numpy.nansum(b_meas**2, axis=0)
    }

  return stats

def calcs_write(b_sats, pkl_dir, pkl):
  basename = os.path.splitext(os.path.basename(pkl))[0]
  file = os.path.join(pkl_dir, f"{basename}.calcs.pkl")
  print(f"  Writing {file}")
  with open(file, "wb") as f:
    pandas.to_pickle(b_sats, f)


def calcs_read(pkl_dir, pkl):
  basename = os.path.splitext(os.path.basename(pkl))[0]
  file = os.path.join(pkl_dir, f"{basename}.calcs.pkl")
  print(f"  Reading {file}")
  with open(file, "rb") as f:
    return pandas.read_pickle(f)


# Number of data points to compute. -1 for all.
n_max = -1

# '0' (IGRF) must be in list
extMags = ['0', 'T89', 'T96']

pkl_dir = "../timeseries-predict/data/raw/satellite-b/files/"


pkls = ["goes8_1996_avg_900_omni.pkl", "goes9_1996_avg_900_omni.pkl"]
for pkl in pkls:
  b_dict = calcs_read(pkl_dir, pkl)
  b_dict['metrics'] = metrics(b_dict['b_meas'], b_dict['b_models'])
  satellite = pkl.split("_")[0]
  plot(b_dict, title=satellite)
  savefig(pkl_dir, pkl)

exit()

for pkl in pkls:

  satellite = pkl.split("_")[0]
  print(f"Processing {satellite}")

  if not os.path.exists(os.path.join(pkl_dir, pkl)):
    raise FileNotFoundError(f"Pickle file {os.path.join(pkl_dir, pkl)}")

  print(f"  Reading {os.path.join(pkl_dir, pkl)}")
  satellite_df = pandas.read_pickle(os.path.join(pkl_dir, pkl))

  times, positions, b_models = compute(satellite_df, extMags, n_max=n_max)

  db_meas = satellite_df[['bx[nT]', 'by[nT]', 'bz[nT]']].values[:n_max]
  # Add IGRF field to get total field for comparison with measurement
  b_meas = db_meas + b_models['0']

  b_dict = {
    'times': times,
    'positions': positions,
    'db_meas': db_meas,
    'b_meas': b_meas,
    'b_models': b_models
  }

  calcs_write(b_dict, pkl_dir, pkl)

  #s = stats(b_meas_tot, b_igrf, b_models)
  #plot(times, b_meas_tot, b_models)