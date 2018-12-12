import time
from .constants import Return
from .events import (
    MsgEvent,
    StringHeadEvent,
    NumberHeadEvent,
    CurrentPageIDHeadEvent
)
from .hook import (
    NexComponents
)

try:
    import serial
    _HAS_PYSERIAL = True
except ImportError:
    _HAS_PYSERIAL = False


A_END_OF_CMD = [0xff, 0xff, 0xff]
S_END_OF_CMD = bytearray(A_END_OF_CMD)


def _format_cmd(cmd):
    return bytearray(cmd, encoding="ASCII") + S_END_OF_CMD


class AbstractSerialNex:
    def __init__(self):
        self.components = NexComponents(self)

    def write(self, cmd):
        print(cmd)
        cmd = _format_cmd(cmd)
        return self.sp.write(cmd)

    def init(self):
        # mode = Return.Mode.NO_RETURN
        # mode = Return.Mode.SUCCESS_ONLY  # production setting
        # mode = Return.Mode.FAIL_ONLY  # default screen setting
        mode = Return.Mode.ALWAYS  # for debug
        msg1 = self.set_cmd_response_mode(mode)
        ret1 = MsgEvent.parse(msg1)
        msg2 = self.send("page 0")
        ret2 = MsgEvent.parse(msg2)
        if mode in [Return.Mode.ALWAYS, Return.Mode.SUCCESS_ONLY]:
            return ret1.issuccess() and ret2.issuccess()
        elif mode in [Return.Mode.FAIL_ONLY, Return.Mode.NO_RETURN]:
            return ret1.isempty() and ret2.isempty()
        else:
            raise NotImplementedError("Undefined mode %s" % mode)

    def set_cmd_response_mode(self, mode):
        assert isinstance(mode, Return.Mode), "Mode must be a Return.Mode enum"
        cmd = "bkcmd=%d" % mode.value
        return self.send(cmd)

    def reset(self):
        cmd = "rest"
        return self.send(cmd)

    def read_all(self):
        return self.sp.read_all()

    def send(self, cmd):
        self.write(cmd)
        time.sleep(0.1)
        return self.read_all()

    def get_nex_string_command(self, cmd):
        return StringHeadEvent.parse(self.send(cmd)).value

    def set_nex_string_command(self, cmd):
        return self.send(cmd)

    def get_nex_number_command(self, cmd, signed, bit_size):
        msg = self.send(cmd)
        evt = NumberHeadEvent.parse(msg)
        if signed:
            return evt.signed_value
        else:
            return evt.value

    def set_nex_number_command(self, cmd):
        return self.send(cmd)

    def get_nex_bool_command(self, cmd):
        msg = self.send(cmd)
        value = NumberHeadEvent.parse(msg).value
        return bool(value)

    def set_nex_bool_command(self, cmd):
        return self.send(cmd)

    @property
    def current_page(self):
        cmd = "sendme"
        msg = self.send(cmd)
        return CurrentPageIDHeadEvent.parse(msg).pid

    def close(self):
        return self.sp.close()

    def poll(self):
        print("poll")
        data = self.read_all()
        print(data)


if _HAS_PYSERIAL:
    class PySerialNex(AbstractSerialNex):
        def __init__(self, *args, **kwargs):
            super().__init__()
            self.sp = serial.Serial(*args, **kwargs)


class NexSerialMock(AbstractSerialNex):
    def __init__(self, *args, **kwargs):
        super().__init__()

    def write(self, cmd):
        pass

    def read(self):
        return None

    def close(self):
        print("close")


"""
# PyBoard 1.1
# https://docs.micropython.org/en/latest/pyboard/pyboard/quickref.html
# RED: VIN
# BLACK: GND
# YELLOW: X9 (Board TX)
# BLUE: X10 (Board RX)

import machine
import time


class uPyNexSerial(AbstractSerialNex):
    def __init__(self, *args, **kwargs):
        self.sp = machine.UART(*args, **kwargs)

"""
