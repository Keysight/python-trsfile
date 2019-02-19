import os
import trsfile
import time
import tempfile
import unittest
import math
import shutil
from trsfile import Trace, SampleCoding, Header, TracePadding

def get_sample(x):
	return math.sin(0.5 * x) * 1000

class TestCreation(unittest.TestCase):

	def setUp(self):
		# We want a tmp file name in a safe way
		fd, self.tmp_path = tempfile.mkstemp(prefix='trsfile_')

		# However, some tests require the file to not yet exist
		os.close(fd)
		os.remove(self.tmp_path)

		# Small guard for windows to prevent some weird race conditions...
		time.sleep(0.01)

	def tearDown(self):
		# Perform any cleanup of the file
		try:
			if os.path.isfile(self.tmp_path):
				os.remove(self.tmp_path)
			elif os.path.isdir(self.tmp_path):
				shutil.rmtree(self.tmp_path, True)
				time.sleep(0.01)
		except FileNotFoundError:
			pass

	def test_write(self):
		trace_count = 100
		sample_count = 1000

		try:
			with trsfile.open(self.tmp_path, 'w', headers = {
					Header.LABEL_X: 'Testing X',
					Header.LABEL_Y: 'Testing Y',
					Header.DESCRIPTION: 'Testing trace creation',
				}, padding_mode = TracePadding.AUTO) as trs_traces:
				trs_traces.extend([
					Trace(
						SampleCoding.FLOAT,
						[0] * sample_count,
						data = i.to_bytes(8, byteorder='big')
					)
					for i in range(0, trace_count)]
				)
		except Exception:
			self.assertTrue(False)

	def test_write_closed(self):
		trace_count = 100
		sample_count = 1000

		with trsfile.open(self.tmp_path, 'w', padding_mode=TracePadding.AUTO) as trs_traces:
			trs_traces.extend([
				Trace(
					SampleCoding.FLOAT,
					[0] * sample_count,
					data = i.to_bytes(8, byteorder='big')
				)
				for i in range(0, trace_count)]
			)

		# Should raise an "ValueError: I/O operation on closed trace set"
		with self.assertRaises(ValueError):
			print(trs_traces)

	def test_read(self):
		trace_count = 100
		sample_count = 1000

		original_traces = [
				Trace(
					SampleCoding.FLOAT,
					[get_sample(i) for i in range(0, sample_count)],
					data = i.to_bytes(8, byteorder='big')
				)
				for i in range(0, trace_count)
			]

		# Create a trace
		with trsfile.open(self.tmp_path, 'w', headers = {
				Header.LABEL_X: 'Testing X',
				Header.LABEL_Y: 'Testing Y',
				Header.DESCRIPTION: 'Testing trace creation',
			}, padding_mode = TracePadding.AUTO
			) as trs_traces:

			trs_traces.extend(original_traces)

			# Make sure length is equal
			self.assertEqual(len(original_traces), len(trs_traces))

		# Read the trace and check if everything is good
		with trsfile.open(self.tmp_path, 'r') as trs_traces:
			# Check if lengths are still good :)
			self.assertEqual(len(original_traces), len(trs_traces))

			# Check if every trace is saved correctly
			for original_trace, trs_trace in zip(trs_traces, original_traces):
				self.assertEqual(original_trace, trs_trace)

	def test_read_non_existing(self):
		with self.assertRaises(FileNotFoundError):
			with trsfile.open(self.tmp_path, 'r') as trs_traces:
				pass

	def test_append(self):
		trace_count = 100
		sample_count = 1000

		# Append to a non-existing file, behaves same as normal "write"
		with trsfile.open(self.tmp_path, 'a', padding_mode=TracePadding.AUTO) as trs_traces:
			self.assertEqual(len(trs_traces), 0)

			# Extend the trace file with 100 traces with each 1000 samples
			trs_traces.extend([
				Trace(
					SampleCoding.FLOAT,
					[0] * sample_count,
					data = i.to_bytes(8, byteorder='big')
				)
				for i in range(0, trace_count)]
			)

			self.assertEqual(len(trs_traces), trace_count)

		# Now open and close for a few times while adding some number of traces
		expected_length = trace_count
		for t in range(0, 10):

			trace_count = (t + 1) * 10

			with trsfile.open(self.tmp_path, 'a', padding_mode=TracePadding.AUTO) as trs_traces:
				self.assertEqual(len(trs_traces), expected_length)

				# Extend the trace file with 100 traces with each 1000 samples
				trs_traces.extend([
					Trace(
						SampleCoding.FLOAT,
						[0] * sample_count,
						data = i.to_bytes(8, byteorder='big')
					)
					for i in range(0, trace_count)]
				)

				expected_length += trace_count
				self.assertEqual(len(trs_traces), expected_length)

	def test_exclusive(self):
		trace_count = 100
		sample_count = 1000

		# Write to file exclusively
		with trsfile.open(self.tmp_path, 'x', padding_mode=TracePadding.AUTO) as trs_traces:
			self.assertEqual(len(trs_traces), 0)

			# Extend the trace file with 100 traces with each 1000 samples
			trs_traces.extend([
				Trace(
					SampleCoding.FLOAT,
					[0] * sample_count,
					data = i.to_bytes(8, byteorder='big')
				)
				for i in range(0, trace_count)]
			)

			self.assertEqual(len(trs_traces), trace_count)

		# Now try again (this should throw an exception)
		with self.assertRaises(FileExistsError):
			with trsfile.open(self.tmp_path, 'x') as trs_traces:
				self.assertEqual(len(trs_traces), trace_count)


	def test_extend(self):
		trace_count = 100
		sample_count = 1000

		with trsfile.open(self.tmp_path, 'w', padding_mode=TracePadding.AUTO) as trs_traces:
			# Extend empty list
			trs_traces.extend([])
			self.assertEqual(len(trs_traces), 0)

			# Extend non empty list
			trs_traces.extend([
				Trace(
					SampleCoding.FLOAT,
					[0] * sample_count,
					data = b'\x00' * 8
				)
				]
			)
			self.assertEqual(len(trs_traces), 1)

			# Extend non empty list
			trs_traces.extend([
				Trace(
					SampleCoding.FLOAT,
					[0] * sample_count,
					data = i.to_bytes(8, byteorder='big')
				)
				for i in range(0, trace_count)]
			)
			self.assertEqual(len(trs_traces), trace_count + 1)

	def test_padding_none(self):
		sample_count = 1000

		with trsfile.open(
			self.tmp_path,
			'w',
			padding_mode = TracePadding.NONE,
			headers = {
				Header.NUMBER_SAMPLES: sample_count,
				Header.LENGTH_DATA: 8,
				Header.SAMPLE_CODING: SampleCoding.FLOAT
			}
			) as trs_traces:
			# This is the length of the trace
			trs_traces.extend(
				Trace(
					SampleCoding.FLOAT,
					[0] * sample_count,
					data = b'\x00' * 8
				)
			)

			# Length is smaller
			with self.assertRaises(ValueError):
				trs_traces.extend(
					Trace(
						SampleCoding.FLOAT,
						[0] * (sample_count - 1),
						data = b'\x10' * 8
					)
				)
			self.assertEqual(len(trs_traces), 1)

			# Length is bigger
			with self.assertRaises(ValueError):
				trs_traces.extend(
					Trace(
						SampleCoding.FLOAT,
						[0] * (sample_count + 1),
						data = b'\x01' * 8
					)
				)
			self.assertEqual(len(trs_traces), 1)

			# Length is equal
			trs_traces.extend(
				Trace(
					SampleCoding.FLOAT,
					[0] * sample_count,
					data = b'\x00' * 8
				)
			)
			self.assertEqual(len(trs_traces), 2)

	def test_padding(self):
		trace_count = 100
		sample_count = 1000
		fmt = SampleCoding.FLOAT

		with trsfile.open(self.tmp_path, 'w', padding_mode=TracePadding.AUTO) as trs_traces:
			# This is the length everything should be padded/clipped to
			trs_traces.extend(
				Trace(
					fmt,
					b'\xDE' * (sample_count * fmt.size),
					data = b'\x00' * 8
				)
			)

			# Padding mode
			trs_traces.extend([
				Trace(
					fmt,
					b'\xDE' * (sample_count + i) * fmt.size,
					data = abs(i).to_bytes(8, byteorder='big')
				)
				for i in range(0, -trace_count, -1)]
			)

			# Clipping mode
			trs_traces.extend([
				Trace(
					fmt,
					b'\xDE' * (sample_count + i) * fmt.size,
					data = i.to_bytes(8, byteorder='big')
				)
				for i in range(0, trace_count)]
			)

		with trsfile.open(self.tmp_path, 'r') as trs_traces:
			self.assertEqual(len(trs_traces), trace_count * 2 + 1)

			# Check that all traces are of the same size
			for trs_trace in trs_traces:
				self.assertEqual(len(trs_trace), sample_count)

			# Check that all padding is zero
			for i, trs_trace in enumerate(trs_traces[1:101]):
				# Difficult case :)
				if i == 0:
					continue

				for si, sample in enumerate(trs_trace[-i:]):
					self.assertEqual(sample, 0.0 if fmt == SampleCoding.FLOAT else 0, str(i))

				# Test that this is indeed not zero
				self.assertNotEqual(trs_trace[-i - 1], 0)

if __name__ == '__main__':
	unittest.main()

