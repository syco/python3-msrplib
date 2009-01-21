import sys
import datetime

# QQQ not used by the library, only by tests

class HeaderLogger:
    """
    >>> l = HeaderLogger()

    >>> l.write_data_with_header('11111', '=====\\n')
    <BLANKLINE>
    =====
    11111

    >>> l.write_data_with_header('22222', '=====\\n')
    <BLANKLINE>
    =====
    22222

    >>> l = HeaderLogger(tell_func = lambda : 1)
    >>> l.write_data_with_header('33333', '-----\\n')
    <BLANKLINE>
    -----
    33333
    >>> l.write_data_with_header('44444', '-----\\n') # will not print header
    44444
    >>> l.write_data_with_header('55555', '-----\\n', True)
    <BLANKLINE>
    -----
    55555
    """
    def __init__(self, write_func=None, tell_func=None, is_enabled_func=None, prefix=''):
        if write_func is not None:
            self._write = write_func
        if tell_func is not None:
            self._tell = tell_func
        if is_enabled_func is not None:
            self._is_enabled = is_enabled_func
        self.prefix = prefix
        self.last_header = None
        self.last_tell = None

    def write_data_with_header(self, msg, header, new_chunk=False):
        if new_chunk:
            self.last_header = None
        if not self._is_enabled():
            return
        assert 'ABC' not in msg
        data = ''
        if header is not None:
            if header != self.last_header or self.last_tell != self._tell():
                data += '\n'
                data += self.prefix + self.header_prefix() + header + '\n' + self.prefix
        msg = msg.replace('\n', '\n' + self.prefix)
        data += msg
        self._write(data)
        self.last_tell = self._tell()
        self.last_header = header

    def header_prefix(self):
        return '%s: ' % (datetime.datetime.now(), )

    def _is_enabled(self):
        return True

    def _tell(self, last_tell=[0]):
        last_tell[0]+=1
        return last_tell[0]

class HeaderLogger_File(HeaderLogger):

    def __init__(self, fileobj=None, is_enabled_func=None, prefix=''):
        if fileobj is None:
            fileobj=sys.stdout
        try:
            fileobj.tell()
        except IOError:
            HeaderLogger.__init__(self, fileobj.write, None, is_enabled_func, prefix=prefix)
        else:
            HeaderLogger.__init__(self, fileobj.write, fileobj.tell, is_enabled_func, prefix=prefix)


class TrafficLogger:

    def __init__(self, header_logger):
        self.header_logger = header_logger

    @classmethod
    def to_file(cls, *args, **kwargs):
        return cls(HeaderLogger_File(*args, **kwargs))

    def report_out(self, data, transport, new_chunk=False):
        try:
            header = transport._header_out
        except AttributeError:
            try:
                header = transport._header_out = '%s --> %s' % self.format_params(transport)
            except Exception, ex:
                header = transport._header_out = '<<<%s %s>>>' % (type(ex).__name__, ex)
        self.header_logger.write_data_with_header(data.replace('\r\n', '\n'), header, new_chunk)

    def report_in(self, data, transport, new_chunk=False):
        try:
            header = transport._header_in
        except AttributeError:
            try:
                header = transport._header_in = '%s <-- %s' % self.format_params(transport)
            except Exception, ex:
                header = transport._header_in = '<<<%s %s>>>' % (type(ex).__name__, ex)
        self.header_logger.write_data_with_header(data.replace('\r\n', '\n'), header, new_chunk)

    def format_params(self, transport):
        return (self.format_address(transport.getHost()),
                self.format_address(transport.getPeer()))

    def format_address(self, addr):
        return "%s:%s" % (addr.host, addr.port)


class StateLogger:

    prefix = 'MSRP: '

    def __init__(self, write_func=None, prefix=None):
        if write_func is not None:
            self._write = write_func
        if prefix is not None:
            self.prefix = prefix

    def _write(self, msg):
        sys.stdout.write(msg + '\n')

    def report_connecting(self, remote_uri):
        msg = '%s%s connecting to %s' % (self.prefix, remote_uri.protocol_name, remote_uri, )
        self._write(msg)

    def report_connected(self, transport):
        msg = '%sConnected to %s:%s' % (self.prefix,
                                        transport.getPeer().host,
                                        transport.getPeer().port)
        self._write(msg)

    def report_disconnected(self, transport, reason):
        msg = '%sClosed connection to %s:%s (%s)' % (self.prefix,
                                                     transport.getPeer().host,
                                                     transport.getPeer().port,
                                                     reason.getErrorMessage())
        self._write(msg)

    def report_listen(self, local_uri, port):
        msg = '%s%s listening on %s:%s' % (self.prefix, local_uri.protocol_name,
                                           port.getHost().host, port.getHost().port)
        self._write(msg)

    def report_accepted(self, local_uri, transport):
        msg = '%s%s accepted from %s:%s on %s:%s' % (self.prefix, local_uri.protocol_name,
                                                     transport.getPeer().host, transport.getPeer().port,
                                                     transport.getHost().host, transport.getHost().port)
        self._write(msg)



class FileWithTell(object):

    def __init__(self, original):
        self.original = original
        self.writecount = 0

    def __getattr__(self, item):
        return getattr(self.original, item)

    def write(self, data):
        self.writecount += len(data)
        return self.original.write(data)

    def writelines(self, lines):
        self.writecount += sum(map(len, lines))
        return self.original.writelines(lines)

    def tell(self):
        return self.writecount

__original_sys_stdout__ = sys.stdout

def hook_std_output():
    "add `tell' method to sys.stdout, so that it's usable with HeaderLogger"
    sys.stdout = FileWithTell(__original_sys_stdout__)

def restore_std_output():
    sys.stdout = __original_sys_stdout__


if __name__=='__main__':
    import doctest
    doctest.testmod()
