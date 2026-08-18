import csv
from locations import Location, locations


distance_table = [[0] * len(locations) for i in range(len(locations))]

with open('distances.txt') as fp:
  line = fp.readline().strip()
  i = 0
  while line:
    strs = line.split(',')
    for j in range(len(strs)):
      distance_table[i][j] = distance_table[j][i] = float(strs[j])
    i += 1
    line = fp.readline().strip()


class Package:
  def __init__(self, package_id, address, city, state, zip_code, deadline, weight, note):
    self.package_id = package_id
    self.address = address
    self.city = city
    self.state = state
    self.zip_code = zip_code
    self.deadline = deadline
    self.weight = weight
    self.note = note

class Truck:
  def __init__(self, truck_id):
    pass

packages = []

with open('packages.csv') as csvfile:
  reader = csv.reader(csvfile)
  next(reader)
  for line in reader:
    packages.append(Package(*line))

