# SaaBluetooth
A (currently scuff) bluetooth sink for an og Saab.

Through the use of an rs485 can hat, a raspberry pi, and some transistor fanagling:
a bluetooth audio sink for an og saab 9-3 (9-5 untested) is possible.


things to note:

this is very scuff

bluetooth on linux is scuff

follow some guide to turn your pi into a bluetooth sink, but dont add any agents
unless your a 10000iq genuis. And use buster instead of ubuntu, suprising but ubuntu
just does not like being a sink. (cough cough i couldnt figure it out)

get some ferrite beads for your wires to reduce noise and signal corruption

the cd connector has BALANCED audio

balanced audio can be achieved with a phase splitter ciruit(sus),
tranformer(whiny), or a impedence balance (quiet). each have benifits
and drawbacks.

if your car doesnt have a cd connector youve been had

the CD changer port has a CONSTANT 12V it is NOT SWITCHED
i have drained my battery and so will yout

and dont be like me and zip tie components to a plywood board
get an actual solution


If you want to go off and add your own stuff heres the holy grail of resources
https://pikkupossu.1g.fi/tomi/projects/i-bus/i-bus.html

