import os
import datetime

import pandas

import spacepy_field

import utilrsw

import gc
gc.set_threshold(10000, 10, 10)


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
    ti, yi = utilrsw.mpl.insert_nans(t, y1[:, i])
    axs[i].plot(ti, yi, 'k', label='measured')
    axs[i].set_ylabel(ylabels[i])
    axs[i].grid(True)
    for midx, model in enumerate(y2.keys()):
      label = model
      if model == '0':
        label = 'IGRF'
      stats = b_dict['metrics'][model]
      label = f"{label} (nans={stats['n_nans'][i]}, PE={stats['pe'][i]:.2f})"
      ti, yi = utilrsw.mpl.insert_nans(t, y2[model][:, i])
      axs[i].plot(ti, yi, label=label)
      axs[i].legend()

  datetick()


def savefig(outfile):
  from matplotlib import pyplot as plt
  file = outfile.replace(".pkl", ".png")
  print(f"  Writing {file}")
  plt.savefig(file, dpi=300, bbox_inches='tight')


def compute(satellite_df, extMag, n_max):

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
    model_name = ""
    if model_name == '0':
      model_name = '(IGRF)'

    print(f"  Calculating model '{extMag}' {model_name}")
    b_models[extMag] = spacepy_field.field(times, positions, extMag, progress=True, grid=False, csys='GSM', intMag=0)


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

  b_dict['metrics'] = metrics(b_dict['b_meas'], b_dict['b_models'])

  return b_dict


def metrics(b_meas, b_models):
  import numpy
  stats = {}
  for model in b_models.keys():
    n_nan = numpy.sum(numpy.isnan(b_models[model]), axis=0)
    num = numpy.nanmean((b_meas - b_models[model])**2, axis=0)
    den = numpy.nanvar(b_meas, axis=0)
    pe = 1 - num/den
    stats[model] = {
      'n_nans': n_nan,
      'mean_error': numpy.nanmean(b_meas - b_models[model], axis=0),
      'mean_abs_error': numpy.nanmean(numpy.abs(b_meas - b_models[model]), axis=0),
      'rmse': numpy.sqrt(numpy.nanmean((b_meas - b_models[model])**2, axis=0)),
      'pe': pe
    }

  return stats


def io_files(pkl_dir, pkl, n_max):
  infile = os.path.join(pkl_dir, pkl)
  basename = os.path.splitext(os.path.basename(pkl))[0]
  n_max_str = f".n_max-{n_max}." if n_max > 0 else "."
  outfile = os.path.join(pkl_dir, f"{basename}.calcs{n_max_str}pkl")
  return infile, outfile


def cli():
  import argparse

  description="Compute and plot magnetic field models for satellite data."
  parser = argparse.ArgumentParser(description=description)
  parser.add_argument(
    "--recalc-field",
    dest="recalc_field",
    action="store_true",
    help="If False, does not calculate models if .calcs.pkl file already exists."
  )
  parser.add_argument(
    "--recalc-metrics",
    dest="recalc_metrics",
    action="store_true",
    help="If True recomputes metrics. Use if metrics() changes."
  )
  parser.add_argument(
    "--plot-only",
    dest="plot_only",
    action="store_true",
    help="If True, only plots from existing .calcs.pkl files."
  )
  parser.add_argument(
    "--n-max",
    dest="n_max",
    type=int,
    default=-1,
    help="Number of data points to compute. If not set, computes for all data points."
  )

  args = parser.parse_args()

  return args

args = cli()

# '0' (IGRF) must be in list
extMags = [
  '0', 'MEAD', 'T87SHORT', 'T87LONG', 'T89', 'T96', 'OPQUIET', 'OPDYN', 'OSTA'
]
extMags = ['0']
pkl_dir = "../timeseries-predict/data/raw/satellite-b/files/"

pkls = ["goes8_1996_avg_900_omni.pkl", "goes9_1996_avg_900_omni.pkl"]


for pkl in pkls:

  satellite = pkl.split("_")[0]
  print(f"Processing {satellite}")

  infile, outfile = io_files(pkl_dir, pkl, args.n_max)

  if args.plot_only and os.path.exists(outfile):
    b_dict = pandas.read_pickle(infile)
    plot(b_dict, title=pkl.split("_")[0])
    savefig(outfile)
    continue

  if not args.recalc_field and os.path.exists(outfile):
    print("  Calculation file exists and recalc=False; not re-calculating field.")
    if not args.recalc_metrics:
      print("  Calculation file exists and args.recalc_metrics=False; not re-calculating metrics.")
    else:
      print("  Calculation file exists but args.recalc_metrics=True; re-calculating metrics.")
      b_dict = pandas.read_pickle(outfile)
      b_dict['metrics'] = metrics(b_dict['b_meas'], b_dict['b_models'])
      pandas.to_pickle(b_dict, outfile)
    continue

  if not os.path.exists(infile):
    raise FileNotFoundError(f"Pickle file {infile}")

  print(f"  Reading {infile}")
  satellite_df = pandas.read_pickle(infile)

  b_dict = compute(satellite_df, extMags, args.n_max)

  print(f"  Writing {outfile}")
  pandas.to_pickle(b_dict, outfile)

  plot(b_dict, title=satellite)

  savefig(outfile)
