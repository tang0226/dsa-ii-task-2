from datetime import datetime, time, timedelta

from timed_entity import TimedEntity
from locations import Location, get_location_by_name, get_location_by_address, distance_table
from package import Package

# The Truck class contains routing logic and history management
# for location and package loading/unloading/delivery
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
  
  def set_driver(self, driver: str):
    self.add_event('set_driver', driver)
    self.driver = driver

  def remove_driver(self):
    self.add_event('remove_driver', self.driver)
    self.driver = None

  def load(self, package: Package):
    # ensure the package is available to load and the truck is not already full
    if package.ready_time and package.ready_time > self.current_time:
      raise ValueError(f'Cannot load Package {package.package_id} into {self}: Package is not present/ready yet')
    if len(self.packages) >= 16:
      raise ValueError(f'Cannot load Package {package.package_id} into {self}: Truck is full')

    # load package into self
    self.packages.append(package)
    self.add_event('load', package)

    # add a loading event to the package's history
    package.wait_until(self.current_time)
    package.add_event('loaded', self)


  def unload(self, package: Package):
    # display a message if the package is late
    if isinstance(package.deadline, datetime) and self.current_time > package.deadline:
      print(f'ERROR: Package {package.package_id} was unloaded late')

    # unload package from self
    self.packages.remove(package)
    self.add_event('unload', package)

    # add an unloaded/delivered event to the package's history and update its status
    package.wait_until(self.current_time)
    package.add_event('delivered', self)
    package.status = 'delivered'


  def drive_to(self, new_loc: Location):
    miles = distance_table[self.location.location_id][new_loc.location_id]
    self.location = new_loc
    self.mileage += miles
    # calculate how long it takes the 18 mph truck to travel this distance
    self.wait(timedelta(minutes=miles/(18/60)))
    self.add_event('drive', {'location': new_loc, 'miles': miles, 'mileage': self.mileage})

  def drive_to_address(self, address: str):
    self.drive_to(get_location_by_address(address))

  def drive_to_name(self, name: str):
      self.drive_to(get_location_by_name(name))


  # Route and deliver the truck's current load of packages
  def route(self, return_to_wgu = True):
    # set status of all packages to 'en route'
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
      # estimate mileage at this exact moment by interpolating between the two locations
      mileage = prev_mileage + segment_miles * ((t - prev_arrival) / (next_arrival - prev_arrival))

    return mileage


  def print_status_at_time(self, t: datetime):
    print(f'{self}:')

    last_i = self.get_first_history_i_after_time(t)

    if last_i == 0:
      print(f'  Driver: none')
      print(f'  Location: {str(get_location_by_name("Western Governors University"))}')
      print(f'  Mileage: 0 miles')
      print(f'  Packages: none')
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

    print(f'  Driver: {driver or "none"}')

    loc_text = str(prev_location)
    if next_location and t != prev_arrival:
      loc_text = 'en route\n            ' + loc_text + '\n            v\n            ' + str(next_location)
    print(f'  Location: {loc_text}')

    print(f'  Mileage: {round(mileage, 2)}')

    pkg_str = 'none'
    if ps: pkg_str = f'[{", ".join([p.package_id for p in ps])}]'
    print(f'  Packages: {pkg_str}')


  def print_current_status(self):
    self.print_status_at_time(self.current_time)

