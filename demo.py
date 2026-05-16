import spacepy_field

print("")

print("Available internal field models (id: name):")
for intMag in spacepy_field.internal_models():
  print(f"  {intMag}: {spacepy_field.internal_model_name(intMag)}")

print("")
print("Available external field models (id: name):")
for intMag in spacepy_field.external_models():
  print(f"  '{intMag}': {spacepy_field.external_model_name(intMag)}")


print("")
print("Available external field models (id: name and details):")
for intMag in spacepy_field.external_models():
  print(f"  '{intMag}'\n    {spacepy_field.external_model_name(intMag, details=True)}")

csys    = 'CDMAG' # Input and output coordinate system.
intMags = [0, 1]        # IGRF, Eccentric tilted dipole
extMags = ['0', 'T89']  # IGRF, Tsyganenko 1989

print("")

print("Single time, single position")
time = '1995-01-02T12:00:00'
position = [-1, 0, 0]
for intMag in intMags:
  for extMag in extMags:
    B = spacepy_field.field(time, position, extMag, csys=csys, intMag=intMag)
    spacepy_field.print_results(time, position, B, intMag, extMag, csys)

print("")

print("Multiple times, single position")
times = ['1995-01-02T12:00:00', '1995-01-02T13:00:00']
for intMag in intMags:
  for extMag in extMags:
    B = spacepy_field.field(times, position, extMag, csys, intMag=intMag)
    spacepy_field.print_results(time, position, B, intMag, extMag, csys)

print("")

print("Multiple times, multiple positions")
position2 = [0, -1, 0]
positions = [position, position2]
for intMag in intMags:
  for extMag in extMags:
    B = spacepy_field.field(times, positions, extMag, csys=csys, intMag=intMag)
    spacepy_field.print_results(time, position, B, intMag, extMag, csys)
