The API documentation
=================================

.. module:: trsfile

This part of the documentation covers all the interfaces of trsfile.

Overview
--------

This section gives an overview of the main classes and their descriptions.

.. autofunction:: open

.. autofunction:: trs_open

.. autoclass:: trsfile.trace.Trace

.. autoclass:: trsfile.trace_set.TraceSet

.. autoclass:: trsfile.engine.trs.TrsEngine

.. autoclass:: trsfile.engine.file.FileEngine

.. autoclass:: trsfile.common.Header

.. autoclass:: trsfile.common.SampleCoding

.. autoclass:: trsfile.common.TracePadding


Common
---------------

.. automodule:: trsfile.common
    :members:
    :undoc-members:
    :show-inheritance:


Trace
---------------

.. automodule:: trsfile.trace
    :members:
    :undoc-members:
    :show-inheritance:


TraceSet
---------------

.. automodule:: trsfile.trace_set
    :members:
    :undoc-members:
    :show-inheritance:


Storage Engines
---------------
The TraceSet behaves like a list (it is a list of Traces). Each Trace also behaves like a list (it is a list of samples). This is all on a conceptual level and the storage engine specifies how this conceptual model is translated to a specific file format. This behavior also makes it easy to convert from any (supported) file format to another one.

.. contents::
    :local:

TrsEngine
+++++++++

.. automodule:: trsfile.engine.trs
    :members:
    :undoc-members:
    :show-inheritance:

FileEngine
++++++++++

.. automodule:: trsfile.engine.file
    :members:
    :undoc-members:
    :show-inheritance:

Engine
++++++++++

.. automodule:: trsfile.engine.engine
    :members:
    :undoc-members:
    :show-inheritance:
