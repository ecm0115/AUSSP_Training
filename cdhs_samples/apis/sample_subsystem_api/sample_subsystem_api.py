#!/usr/bin/env python3
"""
Author: Eirik Mulder (ecm0115@auburn.edu)
"""
import math
from enum import Enum
import re
from binascii import hexlify, crc32
from dataclasses import dataclass
from datetime import timedelta
from threading import Lock
from typing import Literal

from serial import Serial  # pyserial library
from collections import namedtuple

CMD_PREFIX = "XT+"
READ_SYMBOL = "R"
WRITE_SYMBOL = "W"
TERMINATOR = "\r"
RESPONSE_RE = re.compile(rb"^((OK|ER)\+(.*)) ([0-9A-F]{8})\r")  # Command formatting regex
BYTEORDER: Literal["little", "big"] = "big"

serial_tuple = namedtuple(typename="serial_tuple", field_names="port baudrate")

# Not a best practice, but using lazy function definition for 1-liner.
is_err = lambda x: isinstance(x, CommandError)


def int2hex(value, size_ascii):
    bits = int(math.ceil(size_ascii / 2))
    bytes = value.to_bytes(bits, byteorder=BYTEORDER)
    result = hexlify(bytes).upper()
    if size_ascii % 2 != 0:
        result = result[1:]
    return result


# Custom exception
class InvalidCRCException(Exception):
    pass


class ResponseStatus(Enum):
    OK = "OK"
    ER = "ER"


# Sample enumeration use for error identification
class CommandError(Enum):
    CMD_error_none = 0x00
    CMD_error_incorrect_length = 0x01
    CMD_error_incorrect_format = 0x02
    CMD_error_incorrect_addr = 0x03
    CMD_error_incorrect_CRC = 0x04
    CMD_error_invalid_CMD_ID = 0x05
    CMD_error_message_too_small = 0x06


# Python dataclasses automatically have an initializer mapping inputs to attributes.
@dataclass
class MessageResponse:
    status: ResponseStatus
    body: bytes
    crc: bytes

    def __str__(self) -> str:
        return f"{self.status.name} - {self.body} - {self.crc}"

    def extract(self):
        if self.status is ResponseStatus.ER:
            return CommandError(int(self.body, 16))
        return self.body


class SampleDevice:
    serial_info: serial_tuple
    executing_command: Lock  # Mutex is utilized to prevent multiple threads writing to serial device simultaneously.

    def __init__(self, serial_port: str, serial_baudrate: int):
        self.serial_info = serial_tuple(serial_port, serial_baudrate)
        self.executing_command = Lock()

    def send_msg(self, message: bytes, read_timeout: timedelta):
        with self.executing_command, Serial(*self.serial_info, timeout=read_timeout.total_seconds()) as port:
            port: Serial
            print(f"Sending {len(message)} bytes...")
            port.write(message)
            print(f"Sent!")
            response = port.read_until(b"\r")
            print(f"Received: {response}")
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
        response_match = RESPONSE_RE.match(response)
        assert response_match is not None
        assert len(response_match.groups()) == 4

        without_crc = response_match.group(1)
        response_status = ResponseStatus(response_match.group(2).decode("ascii"))
        response_body = response_match.group(3)
        sent_crc = response_match.group(4)

        calculated_crc = SampleDevice.generate_crc(without_crc)
        if calculated_crc != sent_crc:
            raise InvalidCRCException()

        extracted = MessageResponse(response_status, response_body, sent_crc).extract()
        return extracted

    def test_command(self):
        """Command ID: 00"""
        response = self.send_command(00, True)
        return response

    def set_sensor_status(self, new_status: bool):
        """Command ID: 1"""
        params = b""
        params += "TRUE" if new_status else "FALSE"
        response = self.send_command(1, True, params=params)


if __name__ == "__main__":
    sample_device = SampleDevice("/dev/ttyS1", 9600)
    sample_device.test_command()
    sample_device.set_sensor_status(True)
