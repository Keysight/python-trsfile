# Inspector Trace Set `.trs` file support in Python
[![Build Status](https://app.travis-ci.com/Riscure/python-trsfile.svg?branch=master)](https://app.travis-ci.com/Riscure/python-trsfile)
[![Documentation Status](https://readthedocs.org/projects/trsfile/badge/)](https://trsfile.readthedocs.io/)

Riscure Inspector uses the `.trs` file format to save and read traces from disk. To better assist reading and writing trace set files from third parties, Riscure published this Python library.

## Quick start
This library supports reading and writing of `.trs` files, but it does not (*yet*) support modifying existing `.trs` files. Both the `TraceSet` and the `Trace` class emulate all the functionality of a `list`, so slice to your heart's content!

### Installation
This library is available on [PyPi](https://www.pypi.org/project/trsfile/) for Python 3 and up. Just add `trsfile` to your `requirements.txt` or install it via the command line:
```shell
pip install trsfile
```

### TRS version 2: Trace (Set) Parameters
As of release 2.0, two additional provisions were added to the .trs format: Trace Set Parameters and Trace Parameters. These can be used to add supplementary (meta)data to your trace set in a structured, yet flexible way. Note that TRS V2 is backwards compatible with TRS V1. However, as can be expected, the additional information will not be available when using a pre-V2 reader.

### Trace Set Parameters
Trace Set Parameters are user-defined key value pairs that can be used to save global information about the trace set. The following types of data can be used (also see trsfile.traceparameter):

     BYTE:   1 byte integer
     SHORT:  2 byte integer
     INT:    4 byte integer
     FLOAT:  4 byte floating point
     LONG:   8 byte integer
     DOUBLE: 8 byte floating point
     STRING: UTF-8 encoded string value

Each type is handled as a list (array) of values, including single values, so please make sure to supply these as such. Also note that all numeric values except for bytes are encoded and decoded as a _signed_ value.

#### Using Trace Set Parameters
Global parameters can be added by creating a `TraceSetParameterMap` object when creating a trace set. This object behaves like a dictionary, although the trs format dictates that keys must always be strings and values any of the supported parameter types. The following python code shows an example:
```python
from trsfile.parametermap import TraceSetParameterMap
import trsfile.traceparameter as tp

parameters = TraceSetParameterMap()
parameters['BYTES'] =  tp.ByteArrayParameter([0, 1, 255])
parameters['SHORTS'] = tp.ShortArrayParameter([1, 1337, -32768, 32767]) 
parameters['INTS'] = tp.IntegerArrayParameter([42, int(1e6)]) 
parameters['FLOATS'] = tp.FloatArrayParameter([0.1, 0.2, 0.3]) 
parameters['LONGS'] = tp.LongArrayParameter([0x7fffffffffffffff])
parameters['DOUBLES'] = tp.DoubleArrayParameter([3.1415926535, 2.718281828])
parameters['STRINGS'] = tp.StringParameter('Lorem ipsum dolor')
``` 

### Trace Parameters
Trace Parameters behave very similar to Trace Set Parameters from a user perspective. They are values that can be added to _every_ trace, describing specific values that can vary between traces. The data types that can be used are the same as for Trace Set Parameters. However, there are several details that are different:

1. The length of the added information *must* be the same for every trace, due to the way in which trs files are stored. This means that the first trace added to the trace set dictates the length of both arrays _and_ strings. If a longer string is added later, it will result in a corrupted trace set.
2. The length of every parameter is saved in the header at creation time, in a structure called `TraceParameterDefinitionMap`. This structure is used when reading out the traces to determine the structure of the included data, and must therefore be consistent with the actual trace parameters to create a valid trace set. This information is _not_ added to the individual traces themselves.
3. Going forward, there will be pre-defined tags used to mark important information:
    - SAMPLES: An alternative for saving the samples of a trace. This may in the future replace the predefined trace structure of title-data-samples.
    - TITLE: An alternative for saving the title of a trace. This may in the future replace the predefined trace structure of title-data-samples.

#### Using Trace Parameters
Local parameters can be added by creating a `TraceParameters` object when creating a trace. The following java code shows an example:
```python
from trsfile import Trace, SampleCoding
from trsfile.parametermap import TraceParameterMap
import trsfile.traceparameter as tp

parameters = TraceParameterMap()
parameters["BYTE"] = tp.ByteArrayParameter([1, 2, 4, 8])
parameters["INT"] = tp.IntegerArrayParameter([42])
parameters["DOUBLE"] = tp.DoubleArrayParameter([3.14, 1.618])
parameters["STRING"] = tp.StringParameter("A string")
Trace(SampleCoding.FLOAT, list(range(100)), parameters, "trace title")
```

Note that the previously mentioned `TraceParameterDefinitionMap` must created consistent with the above parameters and added to the headers:
```python
from trsfile import Header, trs_open
from trsfile.parametermap import TraceParameterDefinitionMap
from trsfile.traceparameter import ParameterType, TraceParameterDefinition

definitions = TraceParameterDefinitionMap()
definitions["BYTE"] = TraceParameterDefinition(ParameterType.BYTE, 4, 0)
definitions["INT"] =  TraceParameterDefinition(ParameterType.INT, 1, 4)
definitions["DOUBLE"] = TraceParameterDefinition(ParameterType.DOUBLE, 1, 8)
definitions["STRING"] = TraceParameterDefinition(ParameterType.STRING, 8, 16)

with trs_open('trace-set.trs', 'w',
              headers = {Header.TRACE_PARAMETER_DEFINITIONS: definitions}):
    pass
```
See below for a more elaborate example on creating trace sets with parameters.

### Reading `.trs` files
```python
import trsfile

with trsfile.open('trace-set.trs', 'r') as traces:
	# Show all headers
	for header, value in traces.get_headers().items():
		print(header, '=', value)
	print()

	# Iterate over the first 25 traces
	for i, trace in enumerate(traces[0:25]):
		print('Trace {0:d} contains {1:d} samples'.format(i, len(trace)))
		print('  - minimum value in trace: {0:f}'.format(min(trace)))
		print('  - maximum value in trace: {0:f}'.format(max(trace)))
```

### Creating `.trs` files
```python
import random, os
from trsfile import trs_open, Trace, SampleCoding, TracePadding, Header
from trsfile.parametermap import TraceParameterMap, TraceParameterDefinitionMap
from trsfile.traceparameter import ByteArrayParameter, ParameterType, TraceParameterDefinition

with trs_open(
		'trace-set.trs',                 # File name of the trace set
		'w',                             # Mode: r, w, x, a (default to x)
		# Zero or more options can be passed (supported options depend on the storage engine)
		engine = 'TrsEngine',            # Optional: how the trace set is stored (defaults to TrsEngine)
		headers = {                      # Optional: headers (see Header class)
			Header.TRS_VERSION: 2,
			Header.SCALE_X: 1e-6,
			Header.SCALE_Y: 0.1,
			Header.DESCRIPTION: 'Testing trace creation',
			Header.TRACE_PARAMETER_DEFINITIONS: TraceParameterDefinitionMap(
				{'parameter': TraceParameterDefinition(ParameterType.BYTE, 16, 0)})
		},
		padding_mode = TracePadding.AUTO,# Optional: padding mode (defaults to TracePadding.AUTO)
		live_update = True               # Optional: updates the TRS file for live preview (small performance hit)
		                                 #   0 (False): Disabled (default)
		                                 #   1 (True) : TRS file updated after every trace
		                                 #   N        : TRS file is updated after N traces
	) as traces:
	# Extend the trace file with 100 traces with each 1000 samples
	traces.extend([
		Trace(
			SampleCoding.FLOAT,
			[random.uniform(-255, 255) for _ in range(0, 1000)],
			TraceParameterMap({'parameter': ByteArrayParameter(os.urandom(16))})
		)
		for _ in range(0, 100)]
	)

	# Replace 5 traces (the slice [0:10:2]) with random length traces.
	# Because we are creating using the TracePadding.PAD mode, all traces
	# will be clipped or padded on the first trace length
	traces[0:10:2] = [
		Trace(
			SampleCoding.FLOAT,
			[random.uniform(0, 255) for _ in range(0, random.randrange(1000))],
			TraceParameterMap({'parameter': ByteArrayParameter(os.urandom(16))}),
			title = 'Clipped trace'
		)
		for _ in range(0, 5)
	]

	# Adding one Trace
	traces.append(
		Trace(
			SampleCoding.FLOAT,
			[random.uniform(-255, 255) for _ in range(0, 1000)],
			TraceParameterMap({'parameter': ByteArrayParameter(os.urandom(16))})
		)
	)

	# We cannot delete traces with the TrsEngine, other engines do support this feature
	#del traces[40:50]

	# We can only change headers with a value that has the same length as the previous value
	# with the TrsEngine, other engines can support dynamically adding, deleting or changing
	# headers.
	#traces.update_header(Header.LABEL_X, 'Time')
	#traces.update_header(Header.LABEL_Y, 'Voltage')
	#traces.update_header(Header.DESCRIPTION, 'Traces created for some purpose!')

	print('Total length of new trace set: {0:d}'.format(len(traces)))
```

### Converting `TraceSet` from one type to another
```python
import trsfile

with \
	trsfile.open(
		'trace-set',                  # Previously create trace set
		'r',                          # Read only mode
		engine='FileEngine'           # Using the FileEngine
	) as traces, \
	trsfile.open(                     # Note: TrsEngine is the default
		'trace-set.trs',              # Name of the new trace set
		'w',                          # Write mode
		headers=traces.get_headers()  # Copy the headers
	) as new_traces:
	new_traces.extend(traces)         # Extend the new trace set with the
	                                  # traces from the old trace set
```

## Documentation
The full documentation is available in the `docs` folder with a readable version on [Read the Docs](https://trsfile.readthedocs.io/).

## Contributing

### Testing
The library supports Python `unittest` module and the tests can be executed with the following command:
```
python -m unittest
```

### Creating Releases
We use Github Actions to publish packages to PYPy. Read the [Github docs on how to create a new release](https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository) and trigger the publishing workflow:

## License
[BSD 3-Clause Clear License](https://choosealicense.com/licenses/bsd-3-clause-clear/)
