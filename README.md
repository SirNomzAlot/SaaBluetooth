# SaaBluetooth
A bluetooth sink controller for an og Saab.

Through the use of an rs485 can hat, a raspberry pi, and some transistor fanagling:
a bluetooth audio sink for an og saab 9-3 (9-5 untested) is possible.


Things To Note:

This assumes your pi is setup as a bluetooth auido sink (setup with bluez commands)

Bluez's implementation of the audio sink has not worked well in my experience

Close proximity of auido wires to the CAN bus may cause a tick. Using ferriet beads
is recommended; if the problem persists disable writing to the SID

The cd connector uses balanced audio

Balanced audio can be achieved with a phase splitter ciruit(clipping),
tranformer(whiny), or a impedence balance (quiet). each have benifits
and drawbacks.

Some saabs do not have CD connectors due to greedy dealerships removing them

The CD changer port provides unswitched 12v power, either modify the source,
route a new 12v line, or put a switch in


If you want to modify this for your own purposes, the holy grail of resources
https://pikkupossu.1g.fi/tomi/projects/i-bus/i-bus.html

