#!/usr/bin/env python3
"""
Example subsystem API code. (untested)
Author: Eirik Mulder (ecm0115@auburn.edu)
"""
import math
from binascii import hexlify, crc32
from datetime import timedelta
from serial import Serial  # pyserial library


# Command Syntax:
# WRITE:                XT+W<cmd_id><arguments> <CRC>\r
# READ:                 XT+R<cmd_id><arguments> <CRC>\r
# SUCCESSFUL RESPONSE:  OK+<data> <CRC>\r
# ERROR RESPONSE:       ER+<data> <CRC>\r


CMD_PREFIX = "XT+"  # starting symbol for commands
READ_SYMBOL = "R"   # indicates a read (getting data)
WRITE_SYMBOL = "W"  # indicates a write (setting data)
TERMINATOR = "\n"   # indicates the end of a line
BYTEORDER = "big"   # most significant bit sent first
# RESPONSE_RE = re.compile(rb"^((OK|ER)\+(.*)) ([0-9A-F]{8})\r")  # Command formatting regex
# BYTEORDER: Literal["little", "big"] = "big"

# serial_tuple = namedtuple(typename="serial_tuple", field_names="port baudrate")

# Not a best practice, but using lazy function definition for 1-liner.
# is_err = lambda x: isinstance(x, CommandError)


def convert_int_to_hex(value: int, num_characters: int):
    num_bytes = int(math.ceil(num_characters / 2))  # Uses 2 hex characters per byte
    bytes = value.to_bytes(num_bytes, byteorder=BYTEORDER)  # bytes = 10110101 (some sequence of 8 * num_bytes bits)
    result = hexlify(bytes).upper()  # results = 31AF3B (some sequence of 2 * num_bytes hex digits)
    if result[0] == b"0":  # Chop first character off if it's a 0
        result = result[1:]
    return result


class SampleDevice:
    baudrate: int
    serial_port: str

    def __init__(self, serial_port: str, serial_baudrate: int):
        self.baudrate = serial_baudrate
        self.serial_port = serial_port

    def send_msg(self, message: bytes, read_timeout: timedelta):
        port: Serial = Serial(*self.serial_info, timeout=read_timeout.total_seconds())
        print(f"Sending {len(message)} bytes...")
        port.write(message)
        print(f"Sent!")
        response = port.read_until(b"\r")
        print(f"Received: {response}")
        port.close()
        return response

    def send_command(self, cmd_id: int, write: bool, params: bytes = b"", timeout=timedelta(seconds=1)):
        command = self.generate_command(cmd_id, write, params)
        response = self.send_msg(command, timeout)
        response = self.parse_response(response)
        print(f"Received Response: {response}")
        return response

    @staticmethod
    def generate_crc(command: bytes):
        # CRC32 is used to validate messages
        result = crc32(command)
        result = result.to_bytes(4, byteorder=BYTEORDER)
        result = hexlify(result)
        result = result.upper()
        return result

    @staticmethod
    def generate_command(cmd_id: int, write: bool, params: bytes = b"") -> bytes:
        command_type = WRITE_SYMBOL if write else READ_SYMBOL
        command_id_str = str(cmd_id).zfill(2)
        command_header = f"{CMD_PREFIX}{command_type}{command_id_str}".encode("ascii")
        command_without_crc = command_header + params
        cmd_crc = SampleDevice.generate_crc(command_without_crc)
        command = command_without_crc + b" " + cmd_crc + b"\r"
        return command

    @staticmethod
    def parse_response(response: bytes):
        # SUCCESSFUL RESPONSE:  OK+<data> <CRC>\r
        # ERROR RESPONSE:       ER+<data> <CRC>\r
        response_without_crc, sent_crc = response.rsplit(b" ", 1)
        response_status, response_body = response.split(b"+", 1)
        calculated_crc = SampleDevice.generate_crc(response_without_crc)
        if calculated_crc != sent_crc:
            return None, None

        return response_status, response_body

    def test_command(self):
        """Command ID: 00"""
        status, response_data = self.send_command(0, True)
        if status is None:
            raise RuntimeError("CRC Error!")
        if status == "ER":
            raise RuntimeError("Command Error.")
        return response_data

    def set_sensor_status(self, new_status: bool):
        """Command ID: 1"""
        params = b""
        params += "TRUE" if new_status else "FALSE"
        status, response_data = self.send_command(1, True, params=params)
        if status is None:
            raise RuntimeError("CRC Error!")
        if status == "ER":
            raise RuntimeError("Command Error.")
        return response_data


if __name__ == "__main__":
    # Example port: /dev/ttyS1
    # Example serial baudrate: 9600
    sample_device = SampleDevice("/dev/ttyS1", 9600)
    sample_device.test_command()
    sample_device.set_sensor_status(True)
