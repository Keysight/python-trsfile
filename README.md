# Inspector Trace Set `.trs` file support in Python
[![Build Status](https://travis-ci.com/Riscure/python-trsfile.svg?branch=master)](https://travis-ci.com/Riscure/python-trsfile)
[![Documentation Status](https://readthedocs.org/projects/trsfile/badge/)](https://trsfile.readthedocs.io/)

Riscure Inspector uses the `.trs` file format to save and read traces from disk. To better assist reading and writing trace set files from third parties, Riscure published this Python library.

## Quick start
This library supports reading and writing of `.trs` files, but it does not (*yet*) support modifying existing `.trs` files. Both the `TraceSet` and the `Trace` class emulate all the functionality of a `list`, so slice to your heart's content!

### Installation
This library is available on [PyPi](https://www.pypi.org/project/trsfile/) for Python 3 and up. Just add `trsfile` to your `requirements.txt` or install it via the command line:
```shell
pip install trsfile
```

### Reading `.trs` files
```python
import trsfile

with trsfile.open('trace-set.trs', 'r') as traces:
	# Show all headers
	for header, value in trs_file.get_headers().items():
		print(header, '=', value)
	print()

	# Iterate over the first 25 traces
	for i, trace in enumerate(trs_file[0:25]):
		print('Trace {0:d} contains {1:d} samples'.format(i, len(trace)))
		print('  - minimum value in trace: {0:f}'.format(min(trace)))
		print('  - maximum value in trace: {0:f}'.format(max(trace)))
```

### Creating `.trs` files
```python
import random, os, trsfile
from trsfile import trs_open, Trace, SampleCoding, TracePadding, Header

with trs_open(
		'trace-set.trs',                 # File name of the trace set
		'w',                             # Mode: r, w, x, a (default to x)
		# Zero or more options can be passed (supported options depend on the storage engine)
		engine = 'TrsEngine',            # Optional: how the trace set is stored (defaults to TrsEngine)
		headers = {                      # Optional: headers (see Header class)
			Header.LABEL_X: 'Testing X',
			Header.LABEL_Y: 'Testing Y',
			Header.DESCRIPTION: 'Testing trace creation',
		},
		padding_mode = TracePadding.AUTO,# Optional: padding mode (defaults to TracePadding.AUTO)
		live_update = True               # Optional: updates the TRS file for live preview (small performance hit)
		                                 #   0 (False): Disabled (default)
		                                 #   1 (True) : TRS file updated after every trace
		                                 #   N        : TRS file is updated after N traces
	) as trs_file:
	# Extend the trace file with 100 traces with each 1000 samples
	trs_file.extend([
		Trace(
			SampleCoding.FLOAT,
			[random.uniform(-255, 255) for _ in range(0, 1000)],
			data = os.urandom(16)
		)
		for _ in range(0, 100)]
	)

	# Replace 5 traces (the slice [0:10:2]) with random length traces.
	# Because we are creating using the TracePadding.PAD mode, all traces
	# will be clipped or padded on the first trace length
	trs_file[0:10:2] = [
		Trace(
			SampleCoding.FLOAT,
			[random.uniform(0, 255) for _ in range(0, random.randrange(1000))],
			data = os.urandom(16),
			title = 'Clipped trace'
		)
		for _ in range(0, 5)
	]

	# Adding one Trace
	trs_file.append(
		Trace(
			SampleCoding.FLOAT,
			[random.uniform(-255, 255) for _ in range(0, 1000)],
			data = os.urandom(16)
		)
	)

	# We cannot delete traces with the TrsEngine, other engines do support this feature
	#del trs_file[40:50]

	# We can only change headers with a value that has the same length as the previous value
	# with the TrsEngine, other engines can support dynamically adding, deleting or changing
	# headers.
	#trs_file.update_header(Header.LABEL_X, 'Time')
	#trs_file.update_header(Header.LABEL_Y, 'Voltage')
	#trs_file.update_header(Header.DESCRIPTION, 'Traces created for some purpose!')

	print('Total length of new trace set: {0:d}'.format(len(trs_file)))
```

### Converting `TraceSet` from one type to another
```python
import random, os, trsfile

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

## Testing
The library supports Python `unittest` module and the tests can be executed with the following command:
```
python -m unittest
```

## License
[BSD 3-Clause Clear License](https://choosealicense.com/licenses/bsd-3-clause-clear/)
