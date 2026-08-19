import csv
from datetime import datetime, date, time, timedelta

from locations import Location, locations, get_location_by_address, get_location_by_name
from hashtable import HashTable

TODAY = date.today()

def parse_time_str(time_str: str):
  return datetime.strptime(time_str, '%I:%M %p').time()

def add_today(t: time):
  return datetime.combine(TODAY, t)


# build distance table
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


# Parent class for trucks and packages; both will have histories
class TimedEntity:
  def __init__(self, initial_time = time(0, 0, 0)):
    self.current_time = add_today(initial_time)
    self.history = []

  def add_event(self, event_type: str, event_data = None):
    self.history.append({'time': self.current_time.time(), 'type': event_type, 'data': event_data})

  def wait(self, delta: timedelta):
    self.current_time += delta

  def wait_until(self, t: datetime):
    if t < self.current_time:
      raise ValueError('Entity cannot wait until previous time')
    self.current_time = t


class Package(TimedEntity):
  def __init__(
    self,
    package_id,
    address: str,
    city: str,
    state: str,
    zip_code: str,
    deadline: str,
    weight,
    note: str
  ):
    self.package_id = package_id
    self.address = address
    self.city = city
    self.state = state
    self.zip_code = zip_code
    self.deadline = 'EOD'
    if deadline != 'EOD':
      self.set_deadline(deadline)
    self.arrival = add_today(time(0, 0, 0))
    self.weight = int(weight)
    self.note = note
    self.status = 'at hub'
    if 'Delayed' in note:
      self.status = 'delayed'
    
    super().__init__()

  def __repr__(self):
    return str(self.__dict__)

  def set_address(self, address: str):
    self.address = address

  def set_city(self, city: str):
    self.city = city

  def set_zip_code(self, zip_code: str):
    self.zip_code = zip_code

  def set_deadline(self, deadline: str):
    self.deadline = add_today(parse_time_str(deadline))

  def set_arrival(self, arrival: str):
    if self.history:
      raise RuntimeError('Cannot set arrival time of Package with history')
    arrival_time = add_today(parse_time_str(arrival))
    self.arrival = arrival_time

    # seed the package's history with its arrival
    self.wait_until(arrival_time)
    self.add_event('arrived')
    self.status = 'at hub'


class Truck(TimedEntity):
  def __init__(self, truck_id):
    self.truck_id = truck_id
    self.driver = None
    self.packages = []
    self.location = get_location_by_name('Western Governors University')
    self.mileage = 0

    # all trucks start at 8 AM
    super().__init__(time(8, 0, 0))

  def __str__(self):
    return f'Truck {self.truck_id}'

  def __repr__(self):
    return str(self)
  
  def set_driver(self, driver: Driver):
    self.add_event('set_driver', driver)
    self.driver = driver

  def remove_driver(self):
    self.add_event('remove_driver', self.driver)
    self.driver = None

  def load(self, package: Package):
    if package.arrival > self.current_time:
      raise ValueError(f'Cannot load Package {package.package_id} into {self}: Package has not arrived yet')
    if len(self.packages) >= 16:
      raise ValueError(f'Cannot load Package {package.package_id} into {self}: Truck is full')
    
    self.packages.append(package)
    self.add_event('load', package)

    package.wait_until(self.current_time)
    package.add_event('loaded', self)

  def unload(self, package: Package):
    if isinstance(package.deadline, datetime) and self.current_time > package.deadline:
      print(f'ERROR: Package {package.package_id} was unloaded late')

    self.packages.remove(package)
    self.add_event('unload', package)

    package.wait_until(self.current_time)
    package.add_event('unloaded')
    package.status = 'delivered'

  def drive_to(self, new_loc: Location):
    miles = distance_table[self.location.location_id][new_loc.location_id]
    self.location = new_loc
    self.mileage += miles
    self.wait(timedelta(minutes=miles/(18/60)))
    self.add_event('drive', {'location': new_loc, 'miles': miles, 'mileage': self.mileage})

  def drive_to_address(self, address: str):
    self.drive_to(get_location_by_address(address))

  def drive_to_name(self, name: str):
      self.drive_to(get_location_by_name(name))

  def route(self):
    for p in self.packages:
      p.add_event('departed', self)
      p.status = 'en route'

    deadline_pkgs = list(filter(lambda p: p.deadline != 'EOD', self.packages))
    deadline_pkg_ct = len(deadline_pkgs)

    while self.packages:
      search_list = self.packages
      # go to packages with deadlines first
      if deadline_pkg_ct:
        search_list = deadline_pkgs

      # use nearest neighbor algorithm
      min_dist = 10**9
      next_pkg = None

      curr_loc_id = self.location.location_id

      # find the closest location in the search list, then drive to that location
      for p in search_list:
        p_loc_id = get_location_by_address(p.address).location_id
        dist = distance_table[curr_loc_id][p_loc_id]
        if dist < min_dist:
          min_dist = dist
          next_pkg = p
      self.drive_to_address(next_pkg.address)

      # unload all appropriate packages at the current address
      to_unload = filter(lambda p: p.address == next_pkg.address, self.packages)
      for p in to_unload:
        self.unload(p)
        if p in deadline_pkgs:
          deadline_pkgs.remove(p)
          deadline_pkg_ct -= 1
    
    # return to WGU for loading
    self.drive_to_name('Western Governors University')
    


class Driver:
  def __init__(self, name):
    self.name = name

  def __repr__(self):
    return str(self)

  def __str__(self):
    return self.name

packages = HashTable()
with open('packages.csv') as csvfile:
  reader = csv.reader(csvfile)
  next(reader)
  for line in reader:
    package = Package(*line)
    packages.insert(package.package_id, package)

# special packages
packages.get('6').set_arrival('9:05 AM')
packages.get('9').set_address('410 S State St')
packages.get('9').set_city('Salt Lake City')
packages.get('9').set_zip_code('84111')
packages.get('9').set_arrival('10:20 AM')
packages.get('25').set_arrival('9:05 AM')
packages.get('28').set_arrival('9:05 AM')
packages.get('32').set_arrival('9:05 AM')

# truck 1 will prioritize deadlined packages that aren't delayed
batch1 = [packages.get(pid) for pid in [
  # deadlined packages
  '1', '13', '15', '29', '30', '31', '34', '37', '40',
  # other packages
  '2', '4', '5', '7', '8', '10', '11'
]]

# truck 2 will leave as soon as the delayed packages arrive
batch2 = [packages.get(pid) for pid in [
  # delayed, deadlined packages
  '6', '25',
  '14', '16', '20',  # <- must be delivered together
  # other packages
  '3', '18', '36', '38',  # <- must be on truck 2
  '12', '17', '19', '21', '22', '23', '24'
]]

batch3 = [packages.get(pid) for pid in [
  '9', # delayed package with wrong address
  '26', '27', '28', '32', '33', '35', '39'
]]

truck1 = Truck('1')
truck2 = Truck('2')
truck3 = Truck('3')

driver1 = Driver('Alice')
driver2 = Driver('Bob')

truck1.set_driver(driver1)
truck2.set_driver(driver2)

for p in batch1: truck1.load(p)

truck2.wait_until(add_today(parse_time_str('9:05 AM')))
for p in batch2: truck2.load(p)

truck1.route()
truck2.route()

truck_to_vacate = None
if truck1.current_time < truck2.current_time: truck_to_vacate = truck1
else: truck_to_vacate = truck2

truck3.wait_until(truck_to_vacate.current_time)

repeat_driver = truck_to_vacate.driver
truck_to_vacate.remove_driver()
truck3.set_driver(repeat_driver)

for p in batch3: truck3.load(p)
truck3.route()
  