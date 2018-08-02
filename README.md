# Inspector Trace Set `.trs` file support in Python
Riscure Inspector uses the `.trs` file format to save and read traces from disk. To better assist reading and writing trace set files from third parties, Riscure published this Python library.

## Quick start
This library supports reading and writing of `.trs` files, but it does not (*yet*) support modifying existing `.trs` files. Both the `TrcFile` and the `Trace` class emulate all the functionality of a `list`, so slice to your heart's content!

### Installation
This library is available on [PyPi](https://www.pypi.org/project/trsfile/) for Python 3 and up. Just add `trsfile` to your `requirements.txt` or install it via the command line:
```shell
pip install trsfile
```

### Reading `.trs` files
```python
import trsfile

with trsfile.open('new.trs') as trs_file:
	# Show all headers
	for header, value in trs_file.headers.items():
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
import random, os
from trsfile import trs_create, Trace, SampleCoding, TracePadding, Header

with trs_create('new.trs', TracePadding.PAD, force_overwrite = True) as trs_file:
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
	# will be padded to the trace with the biggest length.
	trs_file[0:10:2] = [
		Trace(
			SampleCoding.FLOAT,
			[random.uniform(0, 255) for _ in range(0, random.randrange(1000))],
			data = os.urandom(16),
			title = 'Clipped trace'
		)
		for _ in range(0, 5)
	]

	# Lets delete 10 traces as they are supposedly malformed :)
	del trs_file[40:50]

	# Finally, change some headers, all available headers are defined in the Header class
	trs_file.headers[Header.LABEL_X] = 'Time'
	trs_file.headers[Header.LABEL_Y] = 'Voltage'
	trs_file.headers[Header.DESCRIPTION] = 'Traces created for some purpose!'

	print('Total length of new trace set: {0:d}'.format(len(trs_file)))
```

## Documentation
The full documentation is available in the `doc` folder with a readable version on [readthedocs](https://trsfile.readthedocs.io/en/latest).

## Testing
The library supports Python `unittest` module and the tests can be executed with the following command:
```
python -m unittest
```

## License
[BSD 3-Clause Clear License](https://choosealicense.com/licenses/bsd-3-clause-clear/)
