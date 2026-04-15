import spacepy

import spacepy_field


extMags = spacepy_field.external_models()
extMags = ['0'] # IGRF
intMag = 0 # IGRF
csys = 'CDMAG'


# Single time, single position
time = '1995-01-02T12:00:00'
position = [-1, 0, 0]
for extMag in extMags:
  B = spacepy_field.field(time, position, extMag, csys=csys, intMag=intMag)
  spacepy_field.print_results(time, position, extMag, B, csys, intMag)

# Multiple times, single position
times = ['1995-01-02T12:00:00', '1995-01-02T13:00:00']
for extMag in extMags:
  B = spacepy_field.field(times, position, extMag, csys, intMag=intMag)
  spacepy_field.print_results(times, position, extMag, B, csys, intMag)

# Multiple times, multiple positions
positions = [position, position]
for extMag in extMags:
  B = spacepy_field.field(times, positions, extMag, csys=csys, intMag=intMag)
  spacepy_field.print_results(times, position, extMag, B, csys, intMag)
