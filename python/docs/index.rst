.. legimens documentation master file, created by
   sphinx-quickstart on Sat Apr 25 15:58:29 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Legimens
========

Legimens is a library and a protocol for remote object synchronization.
It can monitor changes in python objects in background, while the main
program is running. It also provides a way to update an object when 
remote provided us updates.

.. code-block:: python

    from legimens import App

    app = App('localhost', 8000)
    app.vars.some_name = 'Mahk'


Determining what data to send
-----------------------------

When dealing with updates of a synchronized object, the important problem is to determine
what data was changed. We don't want to send too coarce updates,
when small change in object triggers large data transmissions.
Fine-grained updates are more data-effificant, but introduce completely and additional overhead.
Legimens provides a way to granually control what data is to be updated and manages the updates for you.

All data is managed in nested dict-like structure, with main root element,
which is accessed as ``.vars`` attribute of Legimens App.

Legimens objects
----------------

The building block of the data tree is :class:`~legimens.Object`.




.. toctree::
   :maxdepth: 2
   :caption: Contents:

   simple_story
   arch


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
