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
    self.history.append({'time': self.current_time, 'type': event_type, 'data': event_data})

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
    self.arrival = None
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

  def get_status_str(self, status: str, timestamp: datetime):
    return {
      'delayed': 'delayed until ',
      'arrived': 'at hub since ',
      'loaded': 'loaded at ',
      'en route': 'en route since ',
      'delivered': 'delivered at ',
    }[status] + time.strftime(timestamp.time(), '%H:%M:%S %p')

  def print_status_at_time(self, t: datetime):
    last_i = 0
    while last_i < len(self.history) and self.history[last_i]['time'] <= t: last_i += 1

    hs = (last_i and self.history[last_i-1::-1]) or []

    status_timestamp = None
    status_str = ''
    for h in hs:
      if h['type'] in ('arrived', 'loaded', 'en route', 'delivered'):
        status_str = self.get_status_str(h['type'], h['time'])
        break

    if not status_str:  # i.e., no history of arrival, loading, traveling, or delivery
      # either the pkg is at the hub w/o delay, or it's delayed and hasn't arrived yet
      status_str = 'at hub'
      if self.arrival:
        status_str = self.get_status_str('delayed', self.arrival)

    truck = ''
    for h in hs:
      if h['type'] == 'delivered':
        break
      if h['type'] == 'loaded':
        truck = h['data']
    print(f'Destination: {get_location_by_address(self.address)}')
    print(f'Status: {status_str}')
    print(f'Truck: {truck or 'none'}')

  def print_current_status(self):
    self.print_status_at_time(self.current_time)

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
    if package.arrival and package.arrival > self.current_time:
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
    package.add_event('delivered', self)
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

  def route(self, return_to_wgu = True):
    for p in self.packages:
      p.add_event('en route', self)
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
    if return_to_wgu:
      self.drive_to_name('Western Governors University')

  def get_first_history_i_after_time(self, t: datetime):
    last_i = 0
    while last_i < len(self.history) and self.history[last_i]['time'] <= t: last_i += 1
    return last_i

  def get_location_at_time(self, t: datetime):
    last_i = self.get_first_history_i_after_time(t)

    # location
    prev_location = None
    prev_arrival = None
    prev_mileage = None
    for i in range(last_i - 1, -1, -1):
      if self.history[i]['type'] == 'drive':
        prev_location = self.history[i]['data']['location']
        prev_arrival = self.history[i]['time']
        prev_mileage = self.history[i]['data']['mileage']
        break

    if prev_location == None:
      prev_location = get_location_by_name('Western Governors University')
      prev_arrival = self.history[0]['time']
      prev_mileage = 0

    next_location = None
    next_arrival = None
    segment_miles = None
    for i in range(last_i, len(self.history)):
      if self.history[i]['type'] == 'drive':
        next_location = self.history[i]['data']['location']
        next_arrival = self.history[i]['time']
        segment_miles = self.history[i]['data']['miles']
        break

    return {
      'prev_location': prev_location,
      'prev_arrival': prev_arrival,
      'prev_mileage': prev_mileage,
      'next_location': next_location,
      'next_arrival': next_arrival,
      'segment_miles': segment_miles,
    }

  def get_mileage_at_time(self, t: datetime):
    last_i = self.get_first_history_i_after_time(t)
    if last_i == 0: return 0

    loc_data = self.get_location_at_time(t)

    prev_location = loc_data['prev_location']
    prev_mileage = loc_data['prev_mileage']
    prev_arrival = loc_data['prev_arrival']

    next_location = loc_data['next_location']
    next_arrival = loc_data['next_arrival']
    segment_miles = loc_data['segment_miles']

    mileage = None
    if next_location == None:
      mileage = prev_mileage
    else:
      mileage = prev_mileage + segment_miles * ((t - prev_arrival) / (next_arrival - prev_arrival))

    return mileage


  def print_status_at_time(self, t: datetime):
    last_i = self.get_first_history_i_after_time(t)

    if last_i == 0:
      print(f'Driver: none')
      print(f'Location: {str(get_location_by_name('Western Governors University'))}')
      print(f'Mileage: 0 miles')
      print(f'Packages: none')
      return

    # driver
    driver = None
    for i in range(last_i - 1, -1, -1):
      if self.history[i]['type'] == 'set_driver':
        driver = self.history[i]['data']
        break
      if self.history[i]['type'] == 'remove_driver':
        break

    # location
    loc_data = self.get_location_at_time(t)

    prev_location = loc_data['prev_location']
    prev_mileage = loc_data['prev_mileage']
    prev_arrival = loc_data['prev_arrival']

    next_location = loc_data['next_location']
    next_arrival = loc_data['next_arrival']
    segment_miles = loc_data['segment_miles']


    # mileage
    mileage = self.get_mileage_at_time(t)

    # calculate packages
    ps = []
    for i in range(last_i):
      h = self.history[i]
      if h['type'] == 'load':
        ps.append(h['data'])
      elif h['type'] == 'unload':
        ps.remove(h['data'])

    print(f'Driver: {driver or 'none'}')

    loc_text = str(prev_location)
    if next_location and t != prev_arrival:
      loc_text = 'en route\n          ' + loc_text + '\n          v\n          ' + str(next_location)
    print(f'Location: {loc_text}')

    print(f'Mileage: {round(mileage, 2)}')

    pkg_str = 'none'
    if ps: pkg_str = f'[{', '.join([p.package_id for p in ps])}]'
    print(f'Packages: {pkg_str}')

  def print_current_status(self):
    self.print_status_at_time(self.current_time)


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

# LOOKUP FUNCTION
def lookup_package(pid: str):
  return packages.get(pid)

# special packages
lookup_package('6').set_arrival('9:05 AM')
lookup_package('9').set_address('410 S State St')
lookup_package('9').set_city('Salt Lake City')
lookup_package('9').set_zip_code('84111')
lookup_package('9').set_arrival('10:20 AM')
lookup_package('25').set_arrival('9:05 AM')
lookup_package('28').set_arrival('9:05 AM')
lookup_package('32').set_arrival('9:05 AM')

# truck 1 will prioritize deadlined packages that aren't delayed
batch1 = [lookup_package(pid) for pid in [
  # deadlined packages
  '1', '13', '15', '29', '30', '31', '34', '37', '40',
  # other packages
  '2', '4', '5', '7', '8', '10', '11'
]]

# truck 2 will leave as soon as the delayed packages arrive
batch2 = [lookup_package(pid) for pid in [
  # delayed, deadlined packages
  '6', '25',
  '14', '16', '20',  # <- must be delivered together
  # other packages
  '3', '18', '36', '38',  # <- must be on truck 2
  '12', '17', '19', '21', '22', '23', '24'
]]

batch3 = [lookup_package(pid) for pid in [
  '9', # delayed package with wrong address
  '26', '27', '28', '32', '33', '35',
]]

trucks = [Truck(str(i)) for i in range(1, 4)]

driver1 = Driver('Alice')
driver2 = Driver('Bob')

trucks[0].set_driver(driver1)
trucks[1].set_driver(driver2)

for p in batch1: trucks[0].load(p)

trucks[1].wait_until(add_today(parse_time_str('9:05 AM')))
for p in batch2: trucks[1].load(p)

trucks[0].route()
trucks[1].route()

truck_to_vacate = None
if trucks[0].current_time < trucks[1].current_time: truck_to_vacate = trucks[0]
else: truck_to_vacate = trucks[1]

trucks[2].wait_until(truck_to_vacate.current_time)

repeat_driver = truck_to_vacate.driver
truck_to_vacate.remove_driver()
trucks[2].set_driver(repeat_driver)

for p in batch3: trucks[2].load(p)
trucks[2].route(return_to_wgu=False)


# CLI

def display_help_msg():
  print("""Available commands: status, quit, help

status:
  displays the status of one or more trucks or packages at a specific (military) time (or end-of-day, if no time is provided)
  truck status includes driver, current / en-route locations, packages, mileage (total mileage shown if multiple trucks are selected)
  package status includes delivery status, truck (if applicable)

  Usage:
    status (truck | package) (<id>[,<id2>,...] | all) [<time>]
  
  Examples:
    status truck 1
    status truck all
    status truck all 10:15
    status package 1,3,5 10:02:30
    status package all 9:45:45

help: displays this help message

quit: exits the program
""")

def parse_ids(s):
  if s == 'all': return s
  ids = s.split(',')
  if ids.count(''):
    return 'Error: missing ID after comma. Make sure no commas are followed by spaces'
  return ids

display_help_msg()

while True:
  full_command = input('> ')
  tokens = list(filter(lambda x: len(x) > 0, full_command.split(' ')))
  command = tokens[0]
  params = tokens[1:]
  if command == 'status':
    if len(params) == 0:
      print('Specify "truck" or "package"')
      continue

    specifier = params[0]
    if specifier != 'truck' and specifier != 'package':
      print(f'Specify "truck" or "package" ("{specifier}" is not a valid specifier)')
      continue

    ids = None
    if len(params) == 1:
      print(f'IDs must be selected after specifier "{specifier}". Add IDs separated by commas without spaces, or add "all" to select all')
      continue
    ids = parse_ids(params[1])
    if isinstance(ids, str) and ids != 'all':
      print(ids)
      continue

    t = None
    if len(params) >= 3:
      for fmt in ['%H:%M', '%H:%M:%S', '%I:%M%P', '%I:%M:%S%P']:
        try:
          t = add_today(time.strptime(params[2], fmt))
          break
        except ValueError:
          pass
      if t == None:
        print(f'Invalid time string "{params[2]}". Please enter a valid time without spaces.')
        continue
      if len(params) >= 4 and params[3].lower() in ('am', 'pm'):
        print(f'Invalid time string "{params[2]} {params[3]}". Please enter a valid time without spaces.')
        continue

    if specifier == 'truck':
      selected = []
      if ids == 'all':
        selected = trucks
      else:
        invalid = False
        for tid in ids:
          if tid == '1':   selected.append(trucks[0])
          elif tid == '2': selected.append(trucks[1])
          elif tid == '3': selected.append(trucks[2])
          else:
            print(f'Invalid truck ID: "{tid}"')
            invalid = True
            break
        if invalid: continue
      if t:
        for truck in selected:
          if len(selected) > 1:
            print(f'{truck}:')
          truck.print_status_at_time(t)
          print()

        if len(selected) > 1:
          total_mileage = sum(tr.get_mileage_at_time(t) for tr in selected)
          print(f'Total mileage: {round(total_mileage, 2)} miles')
      else:
        for truck in selected:
          if len(selected) > 1:
            print(f'{truck}:')
          truck.print_current_status()
          print()

        if len(selected) > 1:
          total_mileage = sum(tr.get_mileage_at_time(tr.current_time) for tr in selected)
          print(f'Total mileage: {round(total_mileage, 2)} miles')

    else: # 'package'
      selected = []
      if ids == 'all':
        selected = sorted(packages.values(), key=lambda p: int(p.package_id))
      else:
        invalid = False
        for pid in ids:
          p = lookup_package(pid)
          if p == None:
            print(f'Invalid package ID: "{pid}"')
            invalid = True
            break
          selected.append(p)
        if invalid:
          continue
      if t:
        for p in selected:
          if len(selected) > 1:
            print(f'Package {p.package_id}:')
          p.print_status_at_time(t)
          print()
      else:
        for p in selected:
          if len(selected) > 1:
            print(f'Package {p.package_id}:')
          p.print_current_status()
          print()

  elif command == 'help':
    display_help_msg()
  elif command == 'quit':
    print('Exiting program...')
    break
  else:
    print(f'Unknown command "{command}"\nType "help" for available commands')


