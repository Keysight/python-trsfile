from trsfile.trace import Trace
from trsfile.engine.engine import Engine

# All our engines
from trsfile.engine.trs import TrsEngine
from trsfile.engine.file import FileEngine

engines = {
    'trsengine': TrsEngine,
    'fileengine': FileEngine,
}
ENGINE = 'engine'


class TraceSet:
    """The :py:obj:`TraceSet` class behaves like a :py:obj:`list`
    object were each item in the list is a :py:obj:`Trace`.

    Storing the :py:obj:`TraceSet` requires knowledge on the format which is
    resolved through the usage of storage engines (:py:obj:`Engine`).
    """

    def __init__(self, path, mode='r', **options):
        # Defaults
        self.engine = None

        # Get the storage engine if one is given, else default to TrsEngine
        engine = options.get(ENGINE, TrsEngine)
        if ENGINE in options:
            del options[ENGINE]

        # We also support engine to be passed as string
        if isinstance(engine, str):
            engine_name = engine.lower()
            if not engine_name.endswith(ENGINE):
                engine_name += ENGINE
            if engine_name not in engines:
                raise ValueError('The storage engine \'{0:s}\'does not exists'.format(engine_name))
            engine = engines[engine_name]

        # Check type
        if not issubclass(engine, Engine):
            raise TypeError('The storage engine has to be of type \'Engine\'')

        self.engine = engine(path, mode, **options)

    def __del__(self):
        self.close()

    def __iter__(self):
        """ reset pointer """
        self.iterator_index = -1
        return self

    def __next__(self):
        self.iterator_index = self.iterator_index + 1

        if self.iterator_index >= len(self):
            raise StopIteration
        return self[self.iterator_index]

    def __enter__(self):
        """Called when entering a `with` block"""
        if self.engine.is_closed():
            raise ValueError('I/O operation on closed trace set')
        return self

    def __exit__(self, *args):
        """Called when exiting a `with` block"""
        self.close()

    def __repr__(self):
        if len(self) <= 0:
            return '<TraceSet (0), empty>'
        else:
            return '<TraceSet ({0:d}), {1:s}, ... ,{2:s}>'.format(len(self), repr(self[0]), repr(self[-1]))

    def __len__(self):
        if self.engine.is_closed():
            raise ValueError('I/O operation on closed trace set')

        return self.engine.length()

    def __delitem__(self, index):
        if self.engine.is_closed():
            raise ValueError('I/O operation on closed trace set')

        if self.engine.is_read_only():
            raise TypeError('Cannot modify trace set, it is (opened) read-only')

        return self.engine.del_traces(index)

    def __setitem__(self, index, traces):
        if self.engine.is_closed():
            raise ValueError('I/O operation on closed trace set')

        if self.engine.is_read_only():
            raise TypeError('Cannot modify trace set, it is (opened) read-only')

        # Make sure we have iterable traces
        if isinstance(traces, Trace):
            traces = [traces]

        # Make sure we only are setting traces
        if any(not isinstance(trace, Trace) for trace in traces):
            raise TypeError('All objects assigned to a trace set needs to be of type \'Trace\'')

        return self.engine.set_traces(index, traces)

    def __getitem__(self, index):
        if self.engine.is_closed():
            raise ValueError('I/O operation on closed trace set')

        traces = self.engine.get_traces(index)

        # Return the select item(s)
        if isinstance(index, slice):
            return traces
        else:
            # Earlier logic should ensure traces contains one element!
            return traces[0]

    def is_closed(self):
        return self.engine.is_closed()

    def close(self):
        if self.engine is not None:
            self.engine.close()

    def append(self, trace):
        self[len(self):len(self)] = trace

    def extend(self, traces):
        self[len(self):len(self)] = traces

    def insert(self, index, trace):
        # TODO: Not yet implemented nicely
        # self[index:index] = trace
        raise NotImplementedError(
            'Insert has not yet been implemented for TraceSet, please raise a Github ticket for priority!')

    def reverse(self):
        return self[::-1]

    def update_headers(self, headers):
        if self.engine.is_closed():
            raise ValueError('I/O operation on closed trace set')

        return self.engine.update_headers(headers)

    def update_header(self, header, value):
        return self.update_headers({header: value})

    def get_headers(self):
        return self.engine.headers

    def get_header(self, header):
        return self.engine.headers[header]

    def __eq__(self, other):
        """Compares two trace sets to each other"""
        if not isinstance(other, TraceSet):
            return False

        if len(self) != len(other):
            return False

        # Not using any, because we want to stop as soon as a difference arises
        for self_trace, other_trace in zip(self, other):
            if self_trace != other_trace:
                return False

        return True
