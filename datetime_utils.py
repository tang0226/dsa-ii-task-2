from datetime import datetime, date, time

TODAY = date.today()

def parse_time_str(time_str: str):
  return datetime.strptime(time_str, '%I:%M %p').time()

# Turn a time object into a datetime object by adding the current date
# (arithmetic operators work on datetime but not on time objects)
def add_date(t: time):
  return datetime.combine(TODAY, t)
