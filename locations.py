from hashtable import HashTable

class Location:
  def __init__(self, location_id, name, address, zip_code):
    self.location_id = location_id
    self.name = name
    self.address = address
    self.zip_code = zip_code

  def __repr__(self):
    return str(self.__dict__)
  def __str__(self):
    return f'{self.name}, {self.address}, {self.zip_code}'


location_data = [
  ['Western Governors University','4001 South 700 East','84107'],
  ['International Peace Gardens','1060 Dalton Ave S','84104'],
  ['Sugar House Park','1330 2100 S','84106'],
  ['Taylorsville-Bennion Heritage City Gov Off','1488 4800 S','84123'],
  ['Salt Lake City Division of Health Services ','177 W Price Ave','84115'],
  ['South Salt Lake Public Works','195 W Oakland Ave','84115'],
  ['Salt Lake City Streets and Sanitation','2010 W 500 S','84104'],
  ['Deker Lake','2300 Parkway Blvd','84119'],
  ['Salt Lake City Ottinger Hall','233 Canyon Rd','84103'],
  ['Columbus Library','2530 S 500 E','84106'],
  ['Taylorsville City Hall','2600 Taylorsville Blvd','84118'],
  ['South Salt Lake Police', '2835 Main St','84115'],
  ['Council Hall','300 State St','84103'],
  ['Redwood Park','3060 Lester St','84119'],
  ['Salt Lake County Mental Health','3148 S 1100 W','84119'],
  ['Salt Lake County/United Police Dept', '3365 S 900 W', '84119'],
  ['West Valley Prosecutor', '3575 W Valley Central Station bus Loop', '84119'],
  ['Housing Auth. of Salt Lake County', '3595 Main St', '84115'],
  ['Utah DMV Administrative Office', '380 W 2880 S', '84115'],
  ['Third District Juvenile Court', '410 S State St', '84111'],
  ['Cottonwood Regional Softball Complex', '4300 S 1300 E', '84117'],
  ['Holiday City Office', '4580 S 2300 E', '84117'],
  ['Murray City Museum', '5025 State St', '84107'],
  ['Valley Regional Softball Complex', '5100 South 2700 West', '84118'],
  ['City Center of Rock Springs', '5383 South 900 East #104', '84117'],
  ['Rice Terrace Pavilion Park', '600 E 900 South', '84105'],
  ['Wheeler Historic Farm', '6351 South 900 East', '84121'],
]

locations = [Location(i, *location_data[i]) for i in range(len(location_data))]


# utility hash tables and lookup functions

address_to_location = HashTable()
for l in locations:
  address_to_location.insert(l.address, l)

def get_location_by_address(addr):
  return address_to_location.get(addr)

name_to_location = HashTable()
for l in locations:
  name_to_location.insert(l.name, l)

def get_location_by_name(name):
  return name_to_location.get(name)


# build distance table, organized by each location's index
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
