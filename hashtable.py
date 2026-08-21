def next_prime(n):
  n += 1
  if (n % 2 == 0): n += 1
  while True:
    is_prime = True
    for f in range(3, int(n ** 0.5) + 1, 2):
      if n % f == 0:
        is_prime = False
        break
    if is_prime:
      return n
    n += 2


INITIAL_SIZE = 7
MAX_COLLISIONS = 10


class HashTable:
  def __init__(self):
    self.table = [None] * INITIAL_SIZE
    self.keys_list = []


  # custom hashing function for ints and strings only
  def get_hash(self, key):
    if isinstance(key, int):
      return (key ** 3) % len(self.table)
    elif isinstance(key, str):
        size = len(self.table)
        n = 1
        for c in key:
          n = (n * ord(c) ** 3 + 3) % size
        return n
    else:
      raise TypeError(f'HashTable key "{key}" is not an integer or string')


  def insert(self, key, val):
    h = b = self.get_hash(key)
    i = 0
    curr = self.table[h]
    while isinstance(curr, tuple) and curr[0] != key:
      i += 1
      if i >= MAX_COLLISIONS:
        self.resize(key, val)
        return True

      # quadratic probing
      b = (h + i + i * i) % len(self.table)
      curr = self.table[b]

    if curr == None or curr[0] != key:
      self.keys_list.append(key)
    self.table[b] = (key, val)


  # finds the index of a filled bucket containing the provided key;
  # used for element retrieval and deletion
  def get_filled_bucket(self, key):
    h = b = self.get_hash(key)
    curr = self.table[h]
    i = 0

    # probe as long as the target slot was occupied or contains the wrong key
    while curr == 'removed' or (isinstance(curr, tuple) and curr[0] != key):
      i += 1
      # if enough filled or removed slots are probed, the key
      # must no longer be present in the table, or else a resize
      # would have taken place
      if i > MAX_COLLISIONS: return None

      # quadratic probing
      b = (h + i + i * i) % len(self.table)
      curr = self.table[b]
    if curr == None: return None
    if not isinstance(self.table[b], tuple):
      raise LookupError(f'Error getting key "{key}" from HashTable')
    return b


  def delete(self, key):
    b = self.get_filled_bucket(key)
    if b == None: return False
    self.table[b] = 'removed'
    self.keys_list.remove(key)


  def get(self, key):
    b = self.get_filled_bucket(key)
    if b == None: return None
    return self.table[b][1]


  def resize(self, next_key, next_val):
    pairs = list(filter(lambda x: isinstance(x, tuple), self.table))
    pairs.append((next_key, next_val))
    self.table = [None] * next_prime(len(self.table) * 2)
    self.keys_list = []
    for p in pairs:
      self.insert(p[0], p[1])


  # return list of keys
  def keys(self):
    return self.keys_list


  # return list of values
  def values(self):
    return [self.get(key) for key in self.keys_list]
  