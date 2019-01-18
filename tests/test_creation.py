import random, os
import trsfile
import time
from trsfile import Trace, SampleCoding, Header

import numpy

import unittest
import trsfile
import os
import binascii
import numpy
from os.path import dirname, abspath
from trsfile import TrsFile, Header, SampleCoding

TMP_TRS_FILE = 'test-trace.trs'

class TestCreation(unittest.TestCase):
	def setUp(self):
		# Make sure no tmp exist
		if os.path.isfile(TMP_TRS_FILE):
			for i in range(0, 10):
				try:
					os.remove(TMP_TRS_FILE)
					break
				except (FileNotFoundError, PermissionError) as e:
					pass
				time.sleep(1)

	def tearDown(self):
		# Make sure no tmp exist
		if os.path.isfile(TMP_TRS_FILE):
			for i in range(0, 10):
				try:
					os.remove(TMP_TRS_FILE)
					break
				except (FileNotFoundError, PermissionError) as e:
					pass
				time.sleep(1)

	def test_write(self):
		trace_count = 100
		sample_count = 1000

		try:
			with trsfile.open(TMP_TRS_FILE, 'w', headers = {
				Header.LABEL_X: 'Testing X',
				Header.LABEL_Y: 'Testing Y',
				Header.DESCRIPTION: 'Testing trace creation',
				}) as trs_traces:
				trs_traces.extend([
					Trace(
						SampleCoding.FLOAT,
						[0] * sample_count,
						data = b'\x00' * 16
					)
					for _ in range(0, trace_count)]
				)
		except Exception:
			self.assertTrue(False)

	def test_read(self):
		trace_count = 100
		sample_count = 1000

		original_traces = [
				Trace(
					SampleCoding.FLOAT,
					[random.uniform(-1000, 1000) for _ in range(0, sample_count)],
					data = os.urandom(16)
				)
				for i in range(0, trace_count)
			]

		# Create a trace
		with trsfile.open(TMP_TRS_FILE, 'w', headers = {
			Header.LABEL_X: 'Testing X',
			Header.LABEL_Y: 'Testing Y',
			Header.DESCRIPTION: 'Testing trace creation',
			}) as trs_traces:

			trs_traces.extend(original_traces)

			# Make sure length is equal
			self.assertEqual(len(original_traces), len(trs_traces))

		# Read the trace and check if everything is good
		with trsfile.open(TMP_TRS_FILE, 'r') as trs_traces:
			# Check if lengths are still good :)
			self.assertEqual(len(original_traces), len(trs_traces))

			# Check if every trace is saved correctly
			for original_trace, trs_trace in zip(trs_traces, original_traces):
				self.assertEqual(original_trace, trs_trace)

	def test_read_non_existing(self):
		with self.assertRaises(FileNotFoundError):
			with trsfile.open(TMP_TRS_FILE, 'r') as trs_traces:
				pass

	def test_append(self):
		trace_count = 100
		sample_count = 1000

		# Append to a non-existing file, behaves same as normal "write"
		with trsfile.open(TMP_TRS_FILE, 'a') as trs_traces:
			self.assertEqual(len(trs_traces), 0)

			# Extend the trace file with 100 traces with each 1000 samples
			trs_traces.extend([
				Trace(
					SampleCoding.FLOAT,
					[0] * sample_count,
					data = b'\x00' * 16
				)
				for _ in range(0, trace_count)]
			)

			self.assertEqual(len(trs_traces), trace_count)

		# Now open and close for a few times while adding random number of traces
		expected_length = trace_count
		for i in range(0, 10):

			trace_count = random.randint(0, 100)

			with trsfile.open(TMP_TRS_FILE, 'a') as trs_traces:
				self.assertEqual(len(trs_traces), expected_length)

				# Extend the trace file with 100 traces with each 1000 samples
				trs_traces.extend([
					Trace(
						SampleCoding.FLOAT,
						[0] * sample_count,
						data = b'\x00' * 16
					)
					for _ in range(0, trace_count)]
				)

				expected_length += trace_count
				self.assertEqual(len(trs_traces), expected_length)

	def test_exclusive(self):
		trace_count = 100
		sample_count = 1000

		# Write to file exclusively
		with trsfile.open(TMP_TRS_FILE, 'x') as trs_traces:
			self.assertEqual(len(trs_traces), 0)

			# Extend the trace file with 100 traces with each 1000 samples
			trs_traces.extend([
				Trace(
					SampleCoding.FLOAT,
					[0] * sample_count,
					data = b'\x00' * 16
				)
				for _ in range(0, trace_count)]
			)

			self.assertEqual(len(trs_traces), trace_count)

		# Now try again (this should throw an exception)
		with self.assertRaises(FileExistsError):
			with trsfile.open(TMP_TRS_FILE, 'x') as trs_traces:
				self.assertEqual(len(trs_traces), trace_count)


	def test_extend(self):
		trace_count = 100
		sample_count = 1000

		with trsfile.open(TMP_TRS_FILE, 'w') as trs_traces:
			# Extend empty list
			trs_traces.extend([])
			self.assertEqual(len(trs_traces), 0)

			# Extend non empty list
			trs_traces.extend([
				Trace(
					SampleCoding.FLOAT,
					[0] * sample_count,
					data = b'\x00' * 16
				)
				]
			)
			self.assertEqual(len(trs_traces), 1)

			# Extend non empty list
			trs_traces.extend([
				Trace(
					SampleCoding.FLOAT,
					[0] * sample_count,
					data = b'\x00' * 16
				)
				for _ in range(0, trace_count)]
			)
			self.assertEqual(len(trs_traces), trace_count + 1)

	def test_padding(self):
		trace_count = 100
		sample_count = 1000
		fmt = SampleCoding.FLOAT

		with trsfile.open(TMP_TRS_FILE, 'w') as trs_traces:
			# This is the length everything should be padded/clipped to
			trs_traces.extend(
				Trace(
					fmt,
					b'\xDE' * (sample_count * fmt.size),
					data = b'\x00' * 16
				)
			)

			# Padding mode
			trs_traces.extend([
				Trace(
					fmt,
					b'\xDE' * (sample_count + i) * fmt.size,
					data = b'\x00' * 16
				)
				for i in range(0, -trace_count, -1)]
			)

			# Clipping mode
			trs_traces.extend([
				Trace(
					fmt,
					b'\xDE' * (sample_count + i) * fmt.size,
					data = b'\x00' * 16
				)
				for i in range(0, trace_count)]
			)

		with trsfile.open(TMP_TRS_FILE, 'r') as trs_traces:
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

