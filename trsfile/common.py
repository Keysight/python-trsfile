from enum import Enum

class TracePadding(Enum):
	"""Defines the padding mode of the samples in each trace. This can be helpful
	when not all traces will be the same length. This can be set in
	:py:func:`trsfile.open()`, :py:func:`trsfile.trs_open()`

	+----------+---------------------------------------------------------------+
	| Mode     | Description                                                   |
	+==========+===============================================================+
	| NONE     | No padding will be used and an exception will be thrown when  |
	|          | traces are not of the same length.                            |
	+----------+---------------------------------------------------------------+
	| PAD      | All traces will be padded with zeroes to the maximum trace    |
	|          | length.                                                       |
	+----------+---------------------------------------------------------------+
	| TRUNCATE | All traces will be truncated to the minimum trace length.     |
	+----------+---------------------------------------------------------------+
	| AUTO     | Traces will be clipped or padded in the best possible way the |
	|          | storage engine supports. This could mean data is lost which   |
	|          | because retroactive padding is not supported.                 |
	+----------+---------------------------------------------------------------+
	"""

	NONE = 0
	PAD = 1
	TRUNCATE = 2
	AUTO = 3

class SampleCoding(Enum):
	"""Defines the encoding of all the samples in the trace.
	Bit 4 specifies if it is a float (1) or an integer (0),
	bits 0 to 3 specifies the length of the value.
	Finally, bits 5-7 are currently reserved and set to 000.

	This class is just a simple lookup table.
	"""

	BYTE  = (0x01, 1, 'int8')
	SHORT = (0x02, 2, 'int16')
	INT   = (0x04, 4, 'int32')
	FLOAT = (0x14, 4, 'float32')

	def __new__(cls, coding, size, format):
		obj = object.__new__(cls)
		obj._value_ = coding
		obj.size = size
		obj.format = format
		return obj

	@property
	def is_float(self):
		return (self._value_ & 0x10) != 0

class Header(Enum):
	"""All headers that are currently supported in the .trs file format as
	defined in the inspector manual (2018). The storage engine shall try to
	always store all headers regardless if they are used or not. However, some
	file formats will have no way of storing arbitrary headers. As such, optional
	headers can be dropped.

	Some headers can be used by :py:class:`trsfile.trace_set.TraceSet` or
	:py:class:`trsfile.trace.Trace` to augment their functionality. An example
	of this	is the :py:meth:`trsfile.trace.Trace.get_key` method.
	"""
	# Enumeration                       Tag   Name  Mandatory Python type   Length  Default value      Description
	NUMBER_TRACES                    = (0x41, 'NT', True,     int,          4,      0,                 'Number of traces')
	NUMBER_SAMPLES                   = (0x42, 'NS', True,     int,          4,      None,              'Number of samples per trace')
	SAMPLE_CODING                    = (0x43, 'SC', True,     SampleCoding, 1,      SampleCoding.BYTE, 'Sample Coding (see SampleCoding class)')
	LENGTH_DATA                      = (0x44, 'DS', False,    int,          2,      None,              'Length of cryptographic data included in trace')
	TITLE_SPACE                      = (0x45, 'TS', False,    int,          1,      255,               'Title space reserved per trace')
	TRACE_TITLE                      = (0x46, 'GT', False,    str,          None,   'trace',           'Global trace title')
	DESCRIPTION                      = (0x47, 'DC', False,    str,          None,   None,              'Description')
	OFFSET_X                         = (0x48, 'XO', False,    int,          4,      0,                 'Offset in X-axis for trace representation')
	LABEL_X                          = (0x49, 'XL', False,    str,          None,   None,              'Label of X-axis')
	LABEL_Y                          = (0x4A, 'YL', False,    str,          None,   None,              'Label of Y-axis')
	SCALE_X                          = (0x4B, 'XS', False,    float,        4,      1,                 'Scale value for X-axis')
	SCALE_Y                          = (0x4C, 'YS', False,    float,        4,      1,                 'Scale value for Y-axis')
	TRACE_OFFSET                     = (0x4D, 'TO', False,    int,          4,      0,                 'Trace offset for displaying trace numbers')
	LOGARITHMIC_SCALE                = (0x4E, 'LS', False,    int,          1,      0,                 'Logarithmic scale')
	ACQUISITION_RANGE_OF_SCOPE       = (0x55, 'RG', False,    float,        4,      0,                 'Range of the scope used to perform acquisition')
	ACQUISITION_COUPLING_OF_SCOPE    = (0x56, 'CL', False,    int,          4,      0,                 'Coupling of the scope used to perform acquisition')
	ACQUISITION_OFFSET_OF_SCOPE      = (0x57, 'OS', False,    float,        4,      0,                 'Offset of the scope used to perform acquisition')
	ACQUISITION_INPUT_IMPEDANCE      = (0x58, 'II', False,    float,        4,      0,                 'Input impedance of the scope used to perform acquisition')
	ACQUISITION_DEVICE_ID            = (0x59, 'AI', False,    bytes,        None,   None,              'Device ID of the scope used to perform acquisition')
	ACQUISITION_TYPE_FILTER          = (0x5A, 'FT', False,    int,          4,      0,                 'The type of filter used during acquisition')
	ACQUISITION_FREQUENCY_FILTER     = (0x5B, 'FF', False,    float,        4,      0,                 'Frequency of the filter used during acquisition')
	ACQUISITION_RANGE_FILTER         = (0x5C, 'FR', False,    float,        4,      0,                 'Range of the filter used during acquisition')
	TRACE_BLOCK                      = (0x5F, 'TB', True,     None,         0,      None,              'Trace block marker: an empty TLV that marks the end of the header')
	EXTERNAL_CLOCK_USED              = (0x60, 'EU', False,    bool,         1,      False,             'External clock used')
	EXTERNAL_CLOCK_THRESHOLD         = (0x61, 'ET', False,    float,        4,      0,                 'External clock threshold')
	EXTERNAL_CLOCK_MULTIPLIER        = (0x62, 'EM', False,    int,          4,      0,                 'External clock multiplier')
	EXTERNAL_CLOCK_PHASE_SHIFT       = (0x63, 'EP', False,    int,          4,      0,                 'External clock phase shift')
	EXTERNAL_CLOCK_RESAMPLER_MASK    = (0x64, 'ER', False,    int,          4,      0,                 'External clock resampler mask')
	EXTERNAL_CLOCK_RESAMPLER_ENABLED = (0x65, 'RE', False,    bool,         1,      False,             'External clock resampler enabled')
	EXTERNAL_CLOCK_FREQUENCY         = (0x66, 'EF', False,    float,        4,      0,                 'External clock frequency')
	EXTERNAL_CLOCK_BASE              = (0x67, 'EB', False,    int,          4,      0,                 'External clock time base')
	NUMBER_VIEW                      = (0x68, 'VT', False,    int,          4,      0,                 'View number of traces: number of traces to show on opening')
	TRACE_OVERLAP                    = (0x69, 'OV', False,    bool,         1,      False,             'Overlap: whether to overlap traces in case of multi trace view')
	GO_LAST_TRACE                    = (0x6A, 'GL', False,    bool,         1,      False,             'Go to last trace on opening')
	INPUT_OFFSET                     = (0x6B, 'IO', False,    int,          4,      0,                 'Input data offset in trace data')
	OUTPUT_OFFSET                    = (0x6C, 'OO', False,    int,          4,      0,                 'Output data offset in trace data')
	KEY_OFFSET                       = (0x6D, 'KO', False,    int,          4,      0,                 'Key data offset in trace data')
	INPUT_LENGTH                     = (0x6E, 'IL', False,    int,          4,      0,                 'Input data length in trace data')
	OUTPUT_LENGTH                    = (0x6F, 'OL', False,    int,          4,      0,                 'Output data length in trace data')
	KEY_LENGTH                       = (0x70, 'KL', False,    int,          4,      0,                 'Key data length in trace data')
	NUMBER_OF_ENABLED_CHANNELS       = (0x71, 'CH', False,    int,          4,      0,                 'Number of oscilloscope channels used for measurement')
	NUMBER_OF_USED_OSCILLOSCOPES     = (0x72, 'NO', False,    int,          4,      0,                 'Number of oscilloscopes used for measurement')
	XY_SCAN_WIDTH                    = (0x73, 'WI', False,    int,          4,      0,                 'Number of steps in the \'x\' direction during XY scan')
	XY_SCAN_HEIGHT                   = (0x74, 'HE', False,    int,          4,      0,                 'Number of steps in the \'y\' direction during XY scan')
	XY_MEASUREMENTS_PER_SPOT         = (0x75, 'ME', False,    int,          4,      0,                 'Number of consecutive measurements done per spot during XY scan')

	def __new__(cls, tag, tag_name, is_mandatory, type, length, default, description):
		obj = object.__new__(cls)
		obj._value_ = tag
		obj.tag_name = tag_name
		obj.is_mandatory = is_mandatory
		obj.type = type
		obj.length = length
		obj.default = default
		obj.description = description
		return obj

	@classmethod
	def has_value(cls, tag):
		return any(tag == item.value for item in cls)

	@classmethod
	def get_mandatory(cls):
		return set([header for header in cls if header.is_mandatory])
