from datetime_utils import add_date
from datetime import datetime, time, timedelta

# Parent class for trucks and packages; both will have histories with single-day timing information
class TimedEntity:
  def __init__(self, initial_time = time(0, 0, 0)):
    self.current_time = add_date(initial_time)
    self.history = []

  def add_event(self, event_type: str, event_data = None):
    self.history.append({'time': self.current_time, 'type': event_type, 'data': event_data})

  def wait(self, delta: timedelta):
    self.current_time += delta

  def wait_until(self, t: datetime):
    if t < self.current_time:
      raise ValueError('Entity cannot wait until previous time')
    self.current_time = t

  # returns the position in the history array where
  #   timestamps first surpass the specified time
  # Used to assist finding an entity's status at a specific time
  def get_first_history_i_after_time(self, t: datetime):
    last_i = 0
    while last_i < len(self.history) and self.history[last_i]['time'] <= t: last_i += 1
    return last_i