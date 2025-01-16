from spacepy_field.spacepy_field import field

if False:
  import spacepy
  spacepy.toolbox.update(leapsecs=True)

if False:
  import logging
  logging.basicConfig(level=logging.INFO)

times = ['1995-01-01T12:00:00']
positions = [[3, 0, 0], [4, 0, 0], [5, 0, 0]]

B = field(times, positions, ['T05', 'TS07'])

print(B)