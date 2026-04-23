import os
import sys

import pandas

import utilrsw
import spacepy_field

import gc
gc.set_threshold(10000, 10, 10)

"""
https://github.com/spacepy/spacepy/blob/main/Doc/source/coordinates.rst:
"... the definitions of an Earth radius differ (SpacePy = 6378.137 km;
IRBEM = 6371.2 km)"
"""
R_E = 6371.2 # km


def cli():
  import argparse

  description="Compute and plot magnetic field models for satellite data."
  parser = argparse.ArgumentParser(description=description)
  parser.add_argument(
    "--recalc-field",
    dest="recalc_field",
    action="store_true",
    help="If set, recomputes SpacePy/IRBEM model fields even if .calcs.pkl file already exists."
  )
  parser.add_argument(
    "--n-max",
    dest="n_max",
    type=int,
    default=-1,
    help="Number of data points to compute. If not set, computes for all data points."
  )
  parser.add_argument(
    "--satellite",
    dest="satellite",
    type=str,
    default="",
    help="If set, only processes files that start with this string (e.g., 'goes' to process all goes satellites or 'goes8')."
  )
  parser.add_argument(
    "--pkl-dir",
    dest="pkl_dir",
    type=str,
    default="../timeseries-predict/data/raw/satellite-b/files/",
    help="Directory containing input .pkl files and where output .calcs.pkl files will be written."
  )
  parser.add_argument(
    "--nn-run-id",
    dest="nn_run_id",
    type=str,
    default="run-0",
    help="NN run ID to read from ../timeseries-predict/data/results/satellite-b/{nn_run_id}/ for adding NN results to b_dict."
  )
  parser.add_argument(
    "--ext-mags",
    dest="extMags",
    type=str,
    nargs="+",
    default=['0', 'MEAD', 'T87SHORT', 'T87LONG', 'T89', 'T96', 'OPQUIET', 'OPDYN', 'OSTA'],
    help="List of external magnetic field models to compute."
  )
  parser.add_argument(
    "--workers",
    dest="workers",
    type=int,
    default=max(1, (os.cpu_count() or 1) // 2),
    help="Number of files to process in parallel. Use 1 to disable parallelism."
  )
  args = parser.parse_args()

  return args


def apply_mask(b_dict, satellite_df, mask):
  import numpy
  mask_array = numpy.asarray(mask, dtype=bool)
  expected_rows = len(b_dict['times'])

  if len(satellite_df) == expected_rows + 1:
    # Old cache has off-by-one in times
    satellite_df = satellite_df.iloc[:expected_rows]

  if len(mask_array) != expected_rows:
    raise ValueError(f"mask has {len(mask_array)} rows but b_dict has {expected_rows} times")

  masked_b_dict = {}
  for key, value in b_dict.items():
    if key == 'b_metrics' or key == 'db_metrics':
      continue
    if key == 'times':
      masked_b_dict[key] = [time for time, keep in zip(value, mask_array) if keep]
      continue
    if key == 'b_models' or key == 'db_models':
      masked_b_dict[key] = {model: values[mask_array] for model, values in value.items()}
      continue
    if key == 'positions' or key == 'b_meas' or key == 'db_meas':
      masked_b_dict[key] = value[mask_array]
      continue
    masked_b_dict[key] = value

  b_dict = masked_b_dict
  satellite_df = satellite_df[mask_array]
  b_dict['b_metrics'] = metrics(b_dict['b_meas'], b_dict['b_models'])
  b_dict['db_metrics'] = metrics(b_dict['db_meas'], b_dict['db_models'])

  return b_dict, satellite_df


def plots(b_dict, satellite_df, out_dir, title="", figsize=(8.5, 12)):

  plot(b_dict, satellite_df, out_dir, db=False, title=title, figsize=figsize)
  plot(b_dict, satellite_df, out_dir, db=True, title=title, figsize=figsize)
  return

  t = list(b_dict['times'])

  # Create one plot per year.
  years = sorted(set(ti.year for ti in t))
  months = sorted(set(ti.month for ti in t))
  for year in years:
    for month in months:
      for day in range(1, 32):
        mask = [ti.year == year and ti.month == month and ti.day == day for ti in t]
        if not any(mask):
          continue
        out_dir = os.path.join(out_dir, 'figures')
        kwargs = {
          "mask": mask,
          "mask_suffix": f"_{year}-{month:02d}-{day:02d}",
          "title": title,
          "figsize": figsize
        }
        plot(b_dict, satellite_df, out_dir, **kwargs)


def plot(b_dict, satellite_df, out_dir, db=False, mask=None, mask_suffix="", title="", figsize=(8.5, 12)):

  import numpy
  import matplotlib
  from matplotlib import pyplot as plt

  from datetick import datetick

  matplotlib.use('Agg')

  plt.rcParams.update({
    'font.family': 'serif',
    'font.serif': ['Times New Roman', 'Times', 'Nimbus Roman No9 L', 'DejaVu Serif'],
    'mathtext.fontset': 'stix',
    'legend.fontsize': 6,
  })

  if mask is not None:
    b_dict, satellite_df = apply_mask(b_dict, satellite_df, mask)

  # Use a local copy so plotting helpers cannot mutate b_dict['times'] in place.
  t = list(b_dict['times'])
  p = b_dict['positions']
  r = (p[:, 0]**2 + p[:, 1]**2 + p[:, 2]**2)**0.5
  rho = (p[:, 0]**2 + p[:, 1]**2)**0.5
  lat = numpy.arctan2(p[:, 2], numpy.sqrt(rho)) * 180 / numpy.pi
  lon = numpy.arctan2(p[:, 1], p[:, 0]) * 180 / numpy.pi

  if db:
    y1 = b_dict['db_meas']
    y2 = b_dict['db_models']
    ylabels = ['$\\Delta B_x$ (nT)', '$\\Delta B_y$ (nT)', '$\\Delta B_z$ (nT)']
  else:
    y1 = b_dict['b_meas']
    y2 = b_dict['b_models']
    ylabels = ['$B_x$ (nT)', '$B_y$ (nT)', '$B_z$ (nT)']

  n_stack = 2 + y1.shape[1]

  fig_t = plt.figure(figsize=figsize)
  gs_t = fig_t.add_gridspec(n_stack, hspace=0.05)
  axs_t = gs_t.subplots(sharex=True)

  fig_s = plt.figure(figsize=(8.5, 8.5))
  gs_s = fig_s.add_gridspec(y1.shape[1])
  axs_s = gs_s.subplots(sharex=False)

  for i in range(n_stack):
    if i == 0:
      axs_t[i].set_title(title)
      R_G = 42164/R_E
      tc, rc = utilrsw.mpl.insert_nans(t, r)
      if title.startswith("GOES"):
        axs_t[i].plot(tc, rc-R_G, 'k')
        axs_t[i].set_ylabel('r - R$_{\\mathrm{G}}$ (R$_{\\mathrm{E}}$)')
      else:
        axs_t[i].plot(tc, rc, 'k')
        axs_t[i].set_ylabel('r (R$_{\\mathrm{E}}$)')
      axs_t[i].grid(True)
      continue

    if i == 1:
      tlat, latc = utilrsw.mpl.insert_nans(t, lat)
      tlon, lonc = utilrsw.mpl.insert_nans(t, lon)
      axs_t[i].plot(tlon, lonc, 'b')
      axs_t[i].plot(tlat, latc, 'k')
      axs_t[i].legend(['Longitude', 'Latitude'])
      axs_t[i].set_ylabel('degrees')
      axs_t[i].grid(True)
      continue

    c = i - 2 # Column index for y1 and y2
    tc, yc = utilrsw.mpl.insert_nans(t, y1[:, c])
    axs_t[i].plot(tc, yc, 'k', label='measured')
    axs_t[i].set_ylabel(ylabels[c])
    axs_t[i].grid(True)

    axs_s[c].set_ylabel(f'{ylabels[c]} predicted')
    if c == y1.shape[1] - 1:
      axs_s[c].set_xlabel(f'measured')
    axs_s[c].grid(True)

    for midx, model in enumerate(y2.keys()):
      label = model
      if model == '0':
        label = 'IGRF'
      if db:
        stats = b_dict['db_metrics'][model]
      else:
        stats = b_dict['b_metrics'][model]
      fn = stats['n_nans'][c]/len(t)
      label = f"{label} (PE={stats['pe'][c]:.2f}; $f_n$={fn:.2f})"
      tc, yc = utilrsw.mpl.insert_nans(t, y2[model][:, c])
      axs_t[i].plot(tc, yc, label=label)
      axs_t[i].legend()
      axs_s[c].plot(y1[:, c], y2[model][:, c], '.', label=label)
      axs_s[c].legend(loc='center left', bbox_to_anchor=(1.02, 0.5))

  for ax in axs_s:
    ax.set_aspect('equal', adjustable='box')
    ax.set_box_aspect(1)

  fig_t.align_ylabels(axs_t)
  datetick(axes=axs_t[-1])

  b_str = "_db" if db else "_b"
  savefig(fig_t, os.path.join(out_dir, f"timeseries{b_str}{mask_suffix}.png"))
  savefig(fig_s, os.path.join(out_dir, f"scatter{b_str}{mask_suffix}.png"))


def savefig(fig, file):
  from matplotlib import pyplot as plt
  print(f"  Writing {file}")
  if not os.path.isdir(os.path.dirname(file)):
    os.makedirs(os.path.dirname(file), exist_ok=True)
  fig.savefig(file, dpi=300, bbox_inches='tight')
  plt.close(fig)


def subset_extMags(requested, computed):

  # Remove any model that is not a SpacePy/IRBEM model.
  spacepy_models = spacepy_field.external_models()
  computed = [m for m in computed if m in spacepy_models]

  # Find models in _requested that are not in _computed.
  needed = [model for model in requested if model not in computed]

  print(f"    Models computed:   {computed}")
  print(f"    Models requested:  {requested}")
  print(f"    Models to compute: {needed}")

  return needed


def satellite_id2name(satellite):
  import re

  s = str(satellite).strip()
  if not s:
    return s

  map = {
    'goes8': 'GOES-8',
    'goes9': 'GOES-9',
    'goes10': 'GOES-10',
    'goes11': 'GOES-11',
    'goes12': 'GOES-12',
    'goes13': 'GOES-13',
    'goes14': 'GOES-14',
    'goes15': 'GOES-15',
    'rbspa': 'RBSP-A',
    'rbspb': 'RBSP-B',
    'themisa': 'THEMIS-A',
    'themisb': 'THEMIS-B',
    'themisc': 'THEMIS-C',
    'themisd': 'THEMIS-D',
    'themise': 'THEMIS-E',
    'polar': 'Polar',
    'imp8': 'IMP-8',
    'geotail': 'Geotail',
    'cluster1': 'Cluster-1',
    'cluster2': 'Cluster-2',
    'cluster3': 'Cluster-3',
    'cluster4': 'Cluster-4'
  }

  return map.get(satellite, satellite)


def io_files(pkl_dir, pkl, n_max):
  in_file = os.path.join(pkl_dir, pkl)
  basename = os.path.splitext(os.path.basename(pkl))[0]
  n_max_str = f"n_max-{n_max}" if n_max > 0 else ""
  if n_max_str:
    n_max_str = f"/{n_max_str}"
  out_file = os.path.join(pkl_dir, f"{basename}{n_max_str}/calcs.pkl")
  if not os.path.isdir(os.path.dirname(out_file)):
    os.makedirs(os.path.dirname(out_file), exist_ok=True)
  return in_file, out_file


def satellite_pkls(pkl_dir, satellite):
  files = os.listdir(pkl_dir)
  pkls = [f for f in files if f.endswith(".pkl") and f.startswith(satellite)]
  if satellite:
    [pkl for pkl in pkls if pkl.startswith(satellite)]
  pkls.sort()
  return pkls


def compute(satellite_df, extMags, n_max):
  import numpy
  import pandas

  # Table 1 in documentation,
  # {pkl_dir}/../doc/Magnetic Field Modeling Database Description Final.pdf,
  # indicates that position and field in GSM.

  if n_max > 0:
    satellite_df = satellite_df.iloc[:n_max]

  positions = (satellite_df[['x[km]', 'y[km]', 'z[km]']].values / R_E).tolist()

  ymdhms = satellite_df[['year', 'month', 'day', 'hour', 'minute', 'second']]
  times = pandas.to_datetime(ymdhms).dt.to_pydatetime().tolist()

  if '0' not in extMags:
    print("  Adding required '0' (IGRF) to extMags.")
    # Need IGRF to get total field; only non-IRGF field included in input files.
    extMags = ['0'] + extMags

  b_models = {}
  for extMag in extMags:


    if extMag == '0':
      print(f"  Calculating '{extMag}' (IGRF)")
    else:
      print(f"  Calculating IGRF + {extMag}")

    kwargs = {
      "progress": True,
      "grid": False,
      "csys": 'GSM',
      "intMag": 0
    }
    b_models[extMag] = spacepy_field.field(times, positions, extMag, **kwargs)


  b_dict = {
    'times': times,
    'positions': numpy.array(positions),
    'b_models': b_models
  }

  return b_dict


def metrics(b_meas, b_models):
  import numpy
  import warnings

  stats = {}
  for model in b_models.keys():
    n_nan = numpy.sum(numpy.isnan(b_models[model]), axis=0)
    if numpy.all(n_nan == b_meas.shape[0]):
      print(f"  Warning: Model '{model}' has NaN values for all data points. Metrics will be NaN.")
    # Temporarily disable RuntimeWarning: Mean of empty slice
    with warnings.catch_warnings():
      warnings.filterwarnings('ignore', message='Mean of empty slice', category=RuntimeWarning)
      mean_error = numpy.nanmean(b_meas - b_models[model], axis=0)
      mean_abs_error = numpy.nanmean(numpy.abs(b_meas - b_models[model]), axis=0)
      rmse = numpy.sqrt(numpy.nanmean((b_meas - b_models[model])**2, axis=0))
      num = numpy.nanmean((b_meas - b_models[model])**2, axis=0)
      den = numpy.nanvar(b_meas, axis=0)
      pe = 1 - num/den
    stats[model] = {
      'n_nans': n_nan,
      'mean_error': mean_error,
      'mean_abs_error': mean_abs_error,
      'rmse': rmse,
      'pe': pe
    }

  return stats


def add_nn_results(satellite_id, b_dict, run_id):

  nn_dir = f"../timeseries-predict/data/results/satellite-b/{run_id}/{satellite_id}/lno/lno.pkl"
  with open(nn_dir, 'rb') as f:
    import pickle
    reps = pickle.load(f)

  start = b_dict['times'][0]
  stop = b_dict['times'][-1]

  measured_train = reps[0]['data']['train']
  measured_test = reps[0]['data']['test']
  predicted_train = reps[0]['models']['nn_mimo']['predicted']['train']
  predicted_test = reps[0]['models']['nn_mimo']['predicted']['test']

  # Combine predicted_train and predicted_test into a single DataFrame with a 'datetime' column.
  # Sort by 'datetime' and then filter to the specified time range.
  predicted = pandas.concat([predicted_train, predicted_test], ignore_index=True)
  predicted = predicted.sort_values('datetime')
  predicted = predicted[(predicted['datetime'] >= start) & (predicted['datetime'] <= stop)]

  measured = pandas.concat([measured_train, measured_test], ignore_index=True)
  measured = measured.sort_values('datetime')
  measured = measured[(measured['datetime'] >= start) & (measured['datetime'] <= stop)]
  measured = measured[['datetime', 'bx', 'by', 'bz']]

  nn_times = pandas.to_datetime(predicted['datetime']).to_numpy()
  b_times = pandas.to_datetime(b_dict['times']).to_numpy()
  if len(nn_times) != len(b_times) or not (nn_times == b_times).all():
    # TODO: Make times the union of b_dict['times'] and predicted['datetime'],
    # and align b_dict['b_meas'] and b_dict['b_models'] with the new times,
    # filling in NaN for any time points that are in one but not the other.
    raise ValueError("NN datetime values do not match b_dict['times']")

  db_model = predicted[['bx', 'by', 'bz']].to_numpy()
  b_dict['db_models']['nn_mimo'] = db_model


def run_one(pkl, pkl_dir, n_max, recalc_field, nn_run_id, extMags):

  satellite_id = pkl.split("_")[0]
  satellite_name = satellite_id2name(satellite_id)

  print(f"Processing {satellite_id} ({satellite_name})")

  in_file, out_file = io_files(pkl_dir, pkl, n_max)

  if not os.path.exists(in_file):
    raise FileNotFoundError(f"Pickle file {in_file}")

  print(f"  Reading db measured from {in_file}")
  satellite_df = pandas.read_pickle(in_file)

  b_dict = None
  extMags_needed = extMags
  if not recalc_field:
    if os.path.exists(out_file):
      print("  Calculation file exists. Reading.")
      b_dict = pandas.read_pickle(out_file)
      extMags_needed = subset_extMags(extMags, b_dict['b_models'].keys())

  if len(extMags_needed) != 0:
    computed_b_dict = compute(satellite_df, extMags_needed, n_max)
    if b_dict is None:
      b_dict = computed_b_dict
    else:
      b_dict['b_models'].update(computed_b_dict['b_models'])

  if b_dict is None:
    raise RuntimeError("No field models were loaded or computed.")

  # At this point, b_dict has keys 'times', 'positions', and 'b_models'
  # (with all requested extMag models). The source for the measurements
  # (Stephens database) only provides db_meas. Compute db for all extMag models.
  b_dict['db_models'] = {}
  for model in b_dict['b_models'].keys():
    b_dict['db_models'][model] = b_dict['b_models'][model] - b_dict['b_models']['0']

  b_dict['db_meas'] = satellite_df[['bx[nT]', 'by[nT]', 'bz[nT]']].values
  if n_max > 0:
    b_dict['db_meas'] = b_dict['db_meas'][:n_max]

  # Add IGRF field to get total field for comparison with measurement.
  # TODO: We don't know if this is the same 'IGRF' field subtracted from
  #       the measurements to get db_meas. This need to be checked.
  b_dict['b_meas'] = b_dict['db_meas'] + b_dict['b_models']['0']

  # Add db_models['nn_mimo'] to b_dict. The NN model predicts db measured from
  # the Stephens database.
  print(f"  Reading db predicted NN results.")
  add_nn_results(satellite_id, b_dict, nn_run_id)
  # Add IGRF field to NN model to get total field for comparison with measurement.
  b_dict['b_models']['nn_mimo'] = b_dict['db_models']['nn_mimo'] + b_dict['b_models']['0']

  print(f"  Calculating metrics.")
  b_dict['b_metrics'] = metrics(b_dict['b_meas'], b_dict['b_models'])
  b_dict['db_metrics'] = metrics(b_dict['db_meas'], b_dict['db_models'])

  print(f"  Writing {out_file}")
  pandas.to_pickle(b_dict, out_file)

  plots(b_dict, satellite_df, os.path.dirname(out_file), title=satellite_name)


def main():
  args = cli()

  extMags = args.extMags

  pkls = satellite_pkls(args.pkl_dir, args.satellite)

  run_args = (args.pkl_dir, args.n_max, args.recalc_field, args.nn_run_id, extMags)
  if args.workers <= 1 or len(pkls) <= 1:
    for pkl in pkls:
      run_one(pkl, *run_args)
  else:
    from concurrent.futures import ProcessPoolExecutor, as_completed
    max_workers = min(args.workers, len(pkls))
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
      futures = {executor.submit(run_one, pkl, *run_args): pkl for pkl in pkls}
      try:
        for future in as_completed(futures):
          pkl = futures[future]
          try:
            future.result()
          except Exception as exc:
            raise RuntimeError(f"Failed processing {pkl}: {exc}") from exc
      except KeyboardInterrupt:
        executor.shutdown(wait=False, cancel_futures=True)
        raise


if __name__ == '__main__':
  try:
    main()
  except KeyboardInterrupt:
    print("\nInterrupted by user (Ctrl+C). Exiting.", file=sys.stderr)

