## Package delivery truck scheduling
A task for my Data Structures and Algorithms II assessment at WGU.

This task involves:
- creating a hash table from scratch
  - I implemented a basic hash table with a custom hash function and quadratic probing for handling collisions.
- calculating optimal truck routes based on a distance table
  - I used the nearest-neighbor algorithm combined with priority selection for time-sensitive packages.
- calculating timing information and managing package deadlines
  - I implemented a `TimedEntity` class with methods for stepping forward in time, adding events, and navigating timestamped history.
  - The `Truck` and `Package` classes extend `TimedEntity` and contain specific methods that search the entity history to determine status, location, and mileage at any time of the day.
- creating an intuitive UI for viewing truck and package statuses at any point in time.
  - I implemented a basic CLI with command and argument parsing.
    ```
    > status package 13,18,26 10:00
    Package 13:
      Address: 2010 W 500 S
      Deadline: 10:30:00 AM
      Status: delivered at 09:14:00 AM
      Truck number: 1
    Package 18:
      Address: 1488 4800 S
      Deadline: EOD
      Status: en route since 09:05:00 AM
      Truck number: 2
    Package 26:
      Address: 5383 South 900 East #104
      Deadline: EOD
      Status: at hub
      Truck number: none
    ```
