from datetime import datetime, time

from timed_entity import TimedEntity
from datetime_utils import add_date, parse_time_str
from locations import get_location_by_address

# Main Package class; instances will be stored in buckets inside of a HashTable
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
    # default to an EOD deadline unless otherwise specified
    self.deadline = 'EOD'
    if deadline != 'EOD':
      self.set_deadline(deadline)
    self.weight = int(weight)
    self.note = note

    # the package starts at the hub unless it has been delayed
    # (the note provides a quick-and-dirty way to check)
    self.status = 'at hub'
    if 'Delayed' in note:
      self.status = 'delayed'

    # can be set via function later
    self.ready_time = None
    
    super().__init__()

  def __repr__(self):
    return str(self.__dict__)

  def set_address(self, address: str):
    self.add_event('set_address', {'new': address, 'old': self.address})
    self.address = address

  def set_city(self, city: str):
    self.city = city

  def set_zip_code(self, zip_code: str):
    self.zip_code = zip_code

  def set_deadline(self, deadline: str):
    self.deadline = add_date(parse_time_str(deadline))

  def set_ready_time(self, ready_time: str):
    if self.history:
      raise RuntimeError('Cannot set ready-time of Package with history')
    t = add_date(parse_time_str(ready_time))
    self.ready_time = t

    # seed the package's history with its ready-time
    self.wait_until(t)
    self.add_event('ready')
    self.status = 'at hub'


  # utility that combines a status with a timestamp in a user-readable format
  def get_status_str(self, status: str, timestamp: datetime):
    status_str = {
      'delayed': 'delayed/not ready until ',
      'ready': 'at hub and ready since ',
      'loaded': 'loaded at ',
      'en route': 'en route since ',
      'delivered': 'delivered at ',
    }[status] + time.strftime(timestamp.time(), '%H:%M:%S %p')
    return status_str


  # searches the package's history to determine its status at the specified time
  def get_status_str_at_time(self, t: datetime):
    # locate the point in the history at which the specified time falls
    last_i = self.get_first_history_i_after_time(t)

    # Create an array that works backwards from last_i
    # for easy back-tracing through the package history
    hs = (last_i and self.history[last_i-1::-1]) or []

    status_str = ''
    for h in hs:
      if h['type'] in ('ready', 'loaded', 'en route', 'delivered'):
        status_str = self.get_status_str(h['type'], h['time'])
        break

    if not status_str:  # i.e., no history of ready-time, loading, traveling, or delivery
      # either the pkg is at the hub without delay, or it was delayed and hasn't arrived yet
      status_str = 'at hub'
      if self.ready_time:
        status_str = self.get_status_str('delayed', self.ready_time)

    return status_str

  def get_current_status_str(self):
    return self.get_status_str_at_time(self.current_time)

  def get_truck_at_time(self, t: datetime):
    loading_time = None
    truck = None
    for h in self.history:
      if h['type'] == 'loaded':
        loading_time = h['time']
        truck = h['data']
        break
    if loading_time and t >= loading_time:
      return truck
    return None

  def get_address_at_time(self, t: datetime):
    address = self.address
    set_address_found = False
    i = 0
    for i in range(len(self.history)):
      if self.history[i]['time'] > t: break
      if self.history[i]['type'] == 'set_address':
        set_address_found = True
        address = self.history[i]['data']['new']
    if not set_address_found:
      while i < len(self.history):
        if self.history[i]['type'] == 'set_address':
          return self.history[i]['data']['old']
        i += 1
    
    return address


  def print_data_at_time(self, t: datetime):
    last_i = self.get_first_history_i_after_time(t)

    print(f'Package {self.package_id}:')
    print(f'  Address: {self.get_address_at_time(t)}')
    print(f'  Deadline: {time.strftime(self.deadline.time(), "%H:%M:%S %p") if self.deadline != "EOD" else "EOD"}')
    print(f'  Status: {self.get_status_str_at_time(t)}')
    print(f'  Truck number: {getattr(self.get_truck_at_time(t), "truck_id", "none")}')

  def print_curr_data(self):
    self.print_data_at_time(self.current_time)