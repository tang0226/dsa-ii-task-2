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

    # the arrival property can be set via function later
    self.arrival = None
    
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
    self.deadline = add_date(parse_time_str(deadline))

  def set_arrival(self, arrival: str):
    if self.history:
      raise RuntimeError('Cannot set arrival time of Package with history')
    arrival_time = add_date(parse_time_str(arrival))
    self.arrival = arrival_time

    # seed the package's history with its arrival
    self.wait_until(arrival_time)
    self.add_event('arrived')
    self.status = 'at hub'

  # utility that combines a status with a timestamp in a user-readable format
  def get_status_str(self, status: str, timestamp: datetime):
    return {
      'delayed': 'delayed until ',
      'arrived': 'at hub since ',
      'loaded': 'loaded at ',
      'en route': 'en route since ',
      'delivered': 'delivered at ',
    }[status] + time.strftime(timestamp.time(), '%H:%M:%S %p')

  # searches the package's history to determine its status at the specified time
  def get_status_at_time_str(self, t: datetime):
    # locate the point in the history at which the specified time falls
    last_i = 0
    while last_i < len(self.history) and self.history[last_i]['time'] <= t: last_i += 1

    # Create an array that works backwards from last_i
    # for easy back-tracing through the package history
    hs = (last_i and self.history[last_i-1::-1]) or []

    status_str = ''
    for h in hs:
      if h['type'] in ('arrived', 'loaded', 'en route', 'delivered'):
        status_str = self.get_status_str(h['type'], h['time'])
        break

    if not status_str:  # i.e., no history of arrival, loading, traveling, or delivery
      # either the pkg is at the hub without delay, or it was delayed and hasn't arrived yet
      status_str = 'at hub'
      if self.arrival:
        status_str = self.get_status_str('delayed', self.arrival)

    return status_str

  def get_current_status_str(self):
    return self.get_status_at_time_str(self.current_time)