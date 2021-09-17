from __future__ import print_function
from contextlib import contextmanager

import struct, array, dbus
import traceback


def struct_to_list(format, *args):
    return dbus.Array(struct.pack(format, *args), signature=dbus.Signature('y'))

@contextmanager
def report_exception_mgr():
    try:
        yield 
    except Exception as e:
        print('Exception',e)


def report_exception(func):
    
    def inner_function(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print('Exception',e)
            traceback.print_exc()
            raise e

    return inner_function


if __name__ == '__main__':
    import binascii
    ssid = binascii.unhexlify('ff80010302')
    signal = 43
    print(struct_to_list('B%dsb' % len(ssid), len(ssid), ssid, signal))    
