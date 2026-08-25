import csv
from datetime import datetime

from hashtable import HashTable
from datetime_utils import parse_time_str, add_date
from package import Package
from truck import Truck


# Initialize the packages hash table and populate it from the CSV file
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
  # deadlined packages
  '14', '16', '20',  # <- must be delivered together
  # other packages
  '3', '18', '36', '38',  # <- must be on truck 2
  '12', '17', '19', '21', '22', '23', '24'
]]

batch3 = [lookup_package(pid) for pid in [
  '9', # delayed package with wrong address
  '26', '27', '28', '32', '33', '35', '39'
]]


# initialize Truck objects (1-3)
trucks = [Truck(str(i)) for i in range(1, 4)]

driver1 = 'Alice'
driver2 = 'Bob'

trucks[0].set_driver(driver1)
trucks[1].set_driver(driver2)


# load the first two trucks
for p in batch1: trucks[0].load(p)

trucks[1].wait_until(add_date(parse_time_str('9:05 AM')))
for p in batch2: trucks[1].load(p)

# dispatch the first two trucks
trucks[0].route()
trucks[1].route()


# determine which truck arrives back first,
# and thus which driver will drive the third truck
truck_to_vacate = None
if trucks[0].current_time < trucks[1].current_time: truck_to_vacate = trucks[0]
else: truck_to_vacate = trucks[1]

trucks[2].wait_until(truck_to_vacate.current_time)

# move the driver to Truck 3
repeat_driver = truck_to_vacate.driver
truck_to_vacate.remove_driver()
trucks[2].set_driver(repeat_driver)

# load and dispatch Truck 3
for p in batch3: trucks[2].load(p)
trucks[2].route(return_to_wgu=False)


# calculate final statistics
delivered_pkg_ct = 0
for p in packages.values():
  if p.status == 'delivered':
    delivered_pkg_ct += 1
ending_time = max([p.current_time for p in packages.values()])
total_mileage = sum([tr.get_mileage_at_time(tr.current_time) for tr in trucks])

# print final statistics
print(f'Packages delivered: {delivered_pkg_ct}')
print(f'Ending time: {datetime.strftime(ending_time, '%I:%M:%S %p')}')
print(f'Total mileage: {round(total_mileage, 2)}')


# CLI

def display_help_msg():
  print("""Available commands: status, quit, help

status:
  displays the status of one or more trucks or packages at a specific time, or end-of-day, if no time is provided)
  IDs must be separated by commas without spaces
  Use the "all" selector to select all trucks or packages

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


# parses a comma-separated ID-list parameter in the CLI
def parse_ids(s):
  if s == 'all': return s
  ids = s.split(',')
  if ids.count(''):
    return 'Error: missing ID after comma. Make sure no commas are followed by spaces'
  return ids


print('\n')
display_help_msg()


while True:
  # input a command and organize its tokens
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
    if len(params) == 1: # i.e. the specifier was the only param and no IDs were provided
      print(f'IDs must be selected after specifier "{specifier}". Add IDs separated by commas without spaces, or add "all" to select all')
      continue
    ids = parse_ids(params[1])
    if isinstance(ids, str) and ids != 'all': # parse_ids returns a string message if it fails
      # print the returned error message
      print(ids)
      continue

    t = None
    if len(params) >= 3:
      # test multiple different formats on the user's input
      for fmt in ['%H:%M', '%H:%M:%S', '%I:%M%P', '%I:%M:%S%P']:
        try:
          t = add_date(datetime.strptime(params[2], fmt).time())
          break
        except ValueError:
          pass
      # display an error if the time input matched no valid formats
      if t == None:
        print(f'Invalid time string "{params[2]}". Please enter a valid time without spaces.')
        continue

      # display an error if the user inserted a space between the time and the "am" or "pm".
      # The time should constitute one token, no spaces
      if len(params) >= 4 and params[3].lower() in ('am', 'pm'):
        print(f'Invalid time string "{params[2]} {params[3]}". Please enter a valid time without spaces.')
        continue


    if specifier == 'truck':
      # build an array of trucks selected by the user
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

      # timestamp specified
      if t:
        for truck in selected:
          truck.print_status_at_time(t)

        # print total mileage of selection after displaying truck status
        if len(selected) > 1:
          total_mileage = sum(tr.get_mileage_at_time(t) for tr in selected)
          print(f'Total mileage: {round(total_mileage, 2)} miles')

      # no timestamp specified: show end-of-day status
      else:
        for truck in selected:
          truck.print_current_status()

        # print total mileage of selection after displaying truck status
        if len(selected) > 1:
          total_mileage = sum(tr.get_mileage_at_time(tr.current_time) for tr in selected)
          print(f'Total mileage: {round(total_mileage, 2)} miles')


    else: # specifier is 'package'
      # build list of packages chosen by the user
      selected = []
      if ids == 'all':
        # the packages hash table entries are not sorted by default
        selected = sorted(packages.values(), key=lambda p: int(p.package_id))
      else:
        # the user provided comma-separated IDs
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

      # timestamp specified
      if t:
        for p in selected:
          p.print_data_at_time(t)
      # no timestamp specified: show end-of-day status
      else:
        for p in selected:
          p.print_curr_data()


  elif command == 'help':
    display_help_msg()
  elif command == 'quit':
    print('Exiting program...')
    # break out of the UI while-loop
    break
  else:
    print(f'Unknown command "{command}"\nType "help" for available commands')
