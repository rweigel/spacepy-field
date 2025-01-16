from spacepy_field.spacepy_field import field

if False:
  import spacepy
  spacepy.toolbox.update(leapsecs=True)

if True:
  import logging
  logging.basicConfig(level=logging.INFO)

times = ['1995-01-02T12:00:00']
#positions = [[3, 0, 0], [4, 0, 0], [5, 0, 0]]
positions = [[-1.15, 2.86, 8.29]]
times = ['2001-01-07T05:15:00']

# TODO: Get from a query to SpacePy:
extMags = ['0', 'ALEX', 'MEAD', 'T87SHORT', 'T87LONG', 'T89', 'OPQUIET', 'OPDYN', 'T96', 'OSTA', 'T01QUIET', 'T01STORM', 'T05', 'TS07']

for extMag in extMags:
  print(80*"-")
  print(f"extMag = {extMag}")
  B = field(times, positions, extMag)
