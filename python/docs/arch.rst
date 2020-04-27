Legimens architechure.
======================

Legimens is built in modular fashion and inspired by unix philosophy.

1. `Server` accepts websocket requests, finds object in `Queue`, serializes object and returns the string.
2.  `Queue` holds pairs ``ref: updates`` that are populated by other propesses. There are two main ways to populate:

    a. Put all objects of interest to queue every ``dt`` seconds
    b. Override ``__setattr__`` of object so it is put to queue every time object is updated.

Both options can either append or refresh the list of updates.

The a. and b. options are usefull for different purposes. A. is analogous to UDP, objects are updated frequently
and we don't want to overwhelm frontend.
B is more like TCP, when we want to flush updates as soon as possible.
