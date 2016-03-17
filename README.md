# pylinda
Linda Module in Python

  Q   B   E   CMD
  F   -   -   Post message to tuplesapce
  T   T   T   Pull message from tuplespace, and remove
  T   T   F   Read message from tuplespace, do not remove
  T   F   T   Take message from tuplespace, else return false
  T   F   F   Peek message if found, else return false

This is a client & server module for adding linda coordination to a python project.

to start a server: 
./linda.py server <port>


to use the client:

import linda
anything = Any(Any) 
c = linda.client.autoconnect(PORT=port)
c.post(('test',1))
print( c.pull(('test',anything))) # returns ('test',1)

