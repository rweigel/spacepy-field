from spacepy_field.spacepy_field import field

if False:
  import spacepy
  spacepy.toolbox.update(leapsecs=True)

if False:
  import logging
  logging.basicConfig(level=logging.INFO)

# TODO: Get from a query to SpacePy:
#extMags = ['0', 'ALEX', 'MEAD', 'T87SHORT', 'T87LONG', 'T89', 'OPQUIET', 'OPDYN', 'T96', 'OSTA', 'T01QUIET', 'T01STORM', 'T05', 'TS07']
extMags = ['0', 'MEAD', 'T87SHORT', 'T87LONG', 'T89', 'OPQUIET', 'T96', 'OSTA', 'T01STORM', 'T05', 'TS07']

extMag = 'TS07'
import pandas

dataframe = pandas.read_pickle("../satellite-predict/sat_data/data/cluster1_2001_avg_300_omni.pkl")
for idx, row in dataframe.iterrows():
  x = row['x[km]']/6378.1
  y = row['y[km]']/6378.1
  z = row['z[km]']/6378.1
  bx = row['bx[nT]']
  by = row['by[nT]']
  bz = row['bz[nT]']
  time = f"{int(row['year'])}-{int(row['month']):02d}-{int(row['day']):02d}T{int(row['hour']):02d}:{int(row['minute']):02d}:00"
  print(f"time: {time} ", end='')
  print(f"position: x: {x:.2f} y: {y:.2f}, z: {z:.2f}")
  print(f"measured    bx: {bx:.2f} by: {by:.2f} bz: {bz:.2f}")

  for extMag in extMags:
    b = field(time, [x, y, z], extMag)
    print(f"{extMag:11s} bx: {b[0]:.2f} by: {b[1]:.2f} bz: {b[2]:.2f}")

  break