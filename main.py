import csv

class Location:
  def __init__(self, name, address, city, state, zip_code):
    self.name = name
    self.address = address
    self.city = city
    self.state = state
    self.zip_code = zip_code

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
  for line in reader:
    packages.append(Package(*line))

