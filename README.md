# Inspector Trace Set `.trs` file support in Python
[![Build Status](https://app.travis-ci.com/Riscure/python-trsfile.svg?branch=master)](https://app.travis-ci.com/Riscure/python-trsfile)
[![Documentation Status](https://readthedocs.org/projects/trsfile/badge/)](https://trsfile.readthedocs.io/)

Riscure Inspector uses the `.trs` file format to save and read traces from disk. To better
assist reading and writing trace set files from third parties, Riscure published this Python
library.

## Quick start
This library supports reading and writing of `.trs` files, but it does not (*yet*) support
modifying existing `.trs` files. Both the `TraceSet` and the `Trace` class emulate all the
functionality of a `list`, so slice to your heart's content!

### Installation
This library is available on [PyPi](https://www.pypi.org/project/trsfile/) for Python 3 and
up. Just add `trsfile` to your `requirements.txt` or install it via the command line:
```shell
pip install trsfile
```

### TRS version 2: Trace (Set) Parameters
As of release 2.0, two additional provisions were added to the .trs format: Trace Set 
Parameters and Trace Parameters. These can be used to add supplementary (meta)data to your
trace set in a structured, yet flexible way. Note that TRS V2 is backwards compatible with
TRS V1. However, as can be expected, the additional information will not be available when
using a pre-V2 reader.

### Trace Set Parameters
Trace Set Parameters are user-defined key value pairs that can be used to save global 
information about the trace set. The following types of data can be used (also see 
trsfile.traceparameter):

     BYTE:   1 byte integer
     SHORT:  2 byte integer
     INT:    4 byte integer
     FLOAT:  4 byte floating point
     LONG:   8 byte integer
     DOUBLE: 8 byte floating point
     STRING: UTF-8 encoded string value

Each type is handled as a list (array) of values, including single values, so please make 
sure to supply these as such. Also note that all numeric values except for bytes are encoded
and decoded as a _signed_ value.

#### Using Trace Set Parameters
Global parameters can be added by creating a `TraceSetParameterMap` object when creating a 
trace set. This object behaves like a dictionary, although the trs format dictates that keys
must always be strings and values any of the supported parameter types. The following python
code shows an example:
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

It is also possible to add parameters to a TraceSetParameterMap with its `add_parameter` 
method. This method deduces the type of parameter from the value that needs to be stored 
in it. A value with the bytes or bytearray type will be stored asa ByteArrayParameter, and 
an array of integers will be stored as either a ShortArrayParameter, an IntegerArrayParameter 
or a LongArrayParameter based on their maximum and minimum value. Any list of numeric values
that includes at least one float value will be stored as a DoubleArrayParameter, because 
python does not distinguish between float and double. The add_parameter (aliased as 'add') 
method also handles the conversion of a singular numeric or boolean value into an array with
a single entry. The following code creates a TraceSetParameterMap very similar to the code 
above using the add_parameter method:

```python
from trsfile.parametermap import TraceSetParameterMap

parameters = TraceSetParameterMap()
parameters.add_parameter('BYTES', bytearray([0, 1, 255]))
parameters.add_parameter('SHORTS', [1, 1337, -32768, 32767]) 
parameters.add_parameter('INTS', [42, int(1e6)]) 
parameters.add('DOUBLES1', [0.1, 0.2, 0.3]) 
parameters.add('LONGS', 0x7fffffffffffffff)
parameters.add('DOUBLES2', [3.1415926535, 2.718281828])
parameters.add('STRINGS', 'Lorem ipsum dolor')
```
The only difference is that add_parameter adds a DoubleArrayParameter instead of a 
FloatArrayParameter, as explained above.

### Trace Parameters
Trace Parameters behave very similar to Trace Set Parameters from a user perspective. They
are values that can be added to _every_ trace, describing specific values that can vary 
between traces. The data types that can be used are the same as for Trace Set Parameters. 
However, there are several details that are different:

1. The length of the added information *must* be the same for every trace, due to the way in
   which trs files are stored. This means that the first trace added to the trace set 
   dictates the length of both arrays _and_ strings. If a longer string is added later, it 
   will result in a corrupted trace set.
2. The length of every parameter is saved in the header when a trace is added to the trace
   set, in a structure called `TraceParameterDefinitionMap`. This structure is used when 
   reading out the traces to determine the structure of the included data, and must therefore
   be consistent with the actual trace parameters to create a valid trace set. This 
   information is _not_ added to the individual traces themselves.
3. Going forward, there will be pre-defined tags used to mark important information:
    - SAMPLES: An alternative for saving the samples of a trace. This may in the future 
      replace the predefined trace structure of title-data-samples.
    - TITLE: An alternative for saving the title of a trace. This may in the future replace 
      the predefined trace structure of title-data-samples.

#### Using Trace Parameters
Local parameters can be added by creating a `TraceParameters` object when creating a trace.
The following java code shows an example:

```python
from trsfile import Trace, SampleCoding
from trsfile.parametermap import TraceParameterMap

parameters = TraceParameterMap()
parameters.add_parameter("BYTE", bytearray([1, 2, 4, 8]))
parameters.add_parameter("SHORT", 42)
parameters.add("DOUBLE", [3.14, 1.618])
parameters.add("STRING", "A string")
Trace(SampleCoding.FLOAT, list(range(100)), parameters, "trace title")
```

Note that the previously mentioned `TraceParameterDefinitionMap` is automatically added to 
the headers when a first Trace is added to a TraceSet. It is also possible to define a 
TraceParameterDefinitionMap and add it to the headers yourself. If you do this, you can 
create Traces with raw trace data instead of a TraceParameterMap. That array of bytes will 
be interpreted as a trace parameter map using your definitions. For that reason, the 
bytearray should have the length that the definition map expects. For example:

```python
from trsfile import Trace, SampleCoding, Header
from trsfile.traceparameter import ParameterType
from trsfile.parametermap import TraceParameterDefinitionMap

headers = {}

parameter_definitions = TraceParameterDefinitionMap()
parameter_definitions.append('INPUT', ParameterType.BYTE, 8) # Add 8 bytes of byte input data to the definitions
parameter_definitions.append('OUTPUT', ParameterType.BYTE, 8) # Add 8 bytes of byte output data after the input data
headers[Header.TRACE_PARAMETER_DEFINITIONS] = parameter_definitions

...

input_output_data = bytes.fromhex('cafebabedeadbeef0102030405060708')
Trace(SampleCoding.FLOAT, list(range(100)), title="trace title", raw_data=input_output_data)

```
The trace created in the above example has an 'INPUT' trace parameter with value 
0xcafebabedeadbeef, and an 'OUTPUT' trace parameter with value 0x0102030405060708. It is 
not recommended to create traces with raw data as input unless you define a trace parameter
definition map, or unless the first trace you add to a trs file does contain a trace 
parameter map (in which case the trace parameter definition map is created implicitly). 

See below for a more elaborate example on creating trace sets with parameters.

### Standard parameters

While working with a trace set, Riscure Inspector and Riscure Inspector FI Python may read 
parameters with specific names to obtain the metadata they need. They then expect this data 
to have a specific type. For example, a TraceSetParameter with the name X_SCALE is expected 
to be a FloatArrayParameter that represents the scale of the X axis of the trace set. 
StandardTraceParameters and StandardTraceSetParameters are enums that specify which 
parameter names are reserved by Riscure tools in this way, and which types those parameters 
should have. It is possible to explicitly add standard parameters to a parameter map using 
its `add_standard_parameter` method. For example:

```python
from trsfile.parametermap import TraceSetParameterMap
from trsfile.standardparameters import StandardTraceSetParameters

parameters = TraceSetParameterMap()
parameters.add_standard_parameter(StandardTraceSetParameters.X_SCALE, 0.1)
parameters.add_standard_parameter(StandardTraceSetParameters.Y_SCALE, 0.5)
parameters.add_standard_parameter(StandardTraceSetParameters.KEY, bytes.fromhex('cafebabedeadbeef'))
```

The `add_standard_parameter` method will throw an error if the given value is not of the type
that the standard parameter expects. When using `add_parameter` to add a parameter with a 
standard parameter name to a map, a similar type-check is performed. However, if the value 
does have the type expected by the standard parameter of that name, only a warning is shown.
It is still recommended that you change either the name or the value of the parameter in
such a case.

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
from trsfile.parametermap import TraceParameterMap, TraceSetParameterMap
from trsfile.traceparameter import ByteArrayParameter
from trsfile.standardparameters import StandardTraceSetParameters

parameters = TraceSetParameterMap()
parameters.add_standard_parameter(StandardTraceSetParameters.X_SCALE, 1e-6)
parameters.add_standard_parameter(StandardTraceSetParameters.Y_SCALE, 0.1)

with trs_open(
		'trace-set.trs',                 # File name of the trace set
		'w',                             # Mode: r, w, x, a (default to x)
		# Zero or more options can be passed (supported options depend on the storage engine)
		engine = 'TrsEngine',            # Optional: how the trace set is stored (defaults to TrsEngine)
		headers = {                      # Optional: headers (see Header class)
			Header.TRS_VERSION: 2,
			Header.DESCRIPTION: 'Testing trace creation',
            Header.TRACE_SET_PARAMETERS: parameters,
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
The full documentation is available in the `docs` folder with a readable version on 
[Read the Docs](https://trsfile.readthedocs.io/).

## Contributing

### Testing
The library supports Python `unittest` module and the tests can be executed with the
following command:
```
python -m unittest
```

### Creating Releases
We use Github Actions to publish packages to PYPy. Read the [Github docs on how to create a new release](https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository) and trigger the publishing workflow:

## License
[BSD 3-Clause Clear License](https://choosealicense.com/licenses/bsd-3-clause-clear/)
