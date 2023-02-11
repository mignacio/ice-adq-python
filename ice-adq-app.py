"""
UART Service
-------------
An example showing how to write a simple program using the Nordic Semiconductor
(nRF) UART service.
"""

#import kivy
import asyncio
import matplotlib.lines as Line2D
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import sys
import json
from itertools import count, takewhile
from typing import Iterator

from bleak import BleakClient, BleakScanner
from bleak.backends.characteristic import BleakGATTCharacteristic
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData
from collections import deque
from matplotlib import style

UART_SERVICE_UUID = "0000ffe0-0000-1000-8000-00805f9b34fb"
UART_RX_CHAR_UUID = "0000ffe0-0000-1000-8000-00805f9b34fb"
UART_TX_CHAR_UUID = "0000ffe1-0000-1000-8000-00805f9b34fb"
START_CHAR = bytes.fromhex("02")
END_CHAR = bytes.fromhex("03")
GROUP_SEPARATOR_CHAR = bytes.fromhex("1D")

#kivy.require('1.9.0')

FoundStart = False
FoundEnd = False
byte_array_buffer = bytearray()

NOTHING_FOUND = 0
FOUND_START = 1
MIDDLE_MESSAGE = 2
FOUND_END = 3
process_byte_packet_state = 0

tace_deque = deque()
tadm_deque = deque()
tesc_deque = deque()

TACE_LABEL = "Tace"
TADM_LABEL = "Tadm"
TESC_LABEL = "Tesc"

def append_packet_to_deque(data: bytearray):
    splitted = data.split(GROUP_SEPARATOR_CHAR)
    decoded_tuple = {int(splitted[0].decode('ascii')), int(splitted[2].decode('ascii'))}
    print(decoded_tuple)
    if splitted[1] == TACE_LABEL:
        tace_deque.append(decoded_tuple)
    elif splitted[1] == TADM_LABEL:
        tadm_deque.append(decoded_tuple)
    elif splitted[1] == TESC_LABEL:
        tesc_deque.append(decoded_tuple)


def process_byte_packet(data: bytearray):
    global process_byte_packet_state, byte_array_buffer

    if process_byte_packet_state == NOTHING_FOUND:
        # empty the buffer
        byte_array_buffer = bytearray(b'')
        start_char_index = data.find(START_CHAR)
        end_char_index = data.find(END_CHAR)
        if start_char_index != -1:
            if start_char_index < end_char_index:
                # We found a start and end in same packet. Just print it.
                append_packet_to_deque(data[start_char_index+1:end_char_index])
                return
            else:
                process_byte_packet_state = FOUND_START
                byte_array_buffer.extend(data[start_char_index+1:])
        else:
            # Guess this wasn't for us
            return
    elif process_byte_packet_state == FOUND_START:
        end_char_index = data.find(END_CHAR)
        if end_char_index != -1:
            process_byte_packet_state = NOTHING_FOUND
            byte_array_buffer.extend(data[:end_char_index])
            append_packet_to_deque(byte_array_buffer)
        else:
            process_byte_packet_state = MIDDLE_MESSAGE
            byte_array_buffer.extend(data)
    elif process_byte_packet_state == MIDDLE_MESSAGE:
        end_char_index = data.find(END_CHAR)
        if end_char_index != -1:
            process_byte_packet_state = NOTHING_FOUND
            byte_array_buffer.extend(data[:end_char_index])
            append_packet_to_deque(byte_array_buffer)
        else:
            byte_array_buffer.extend(data)


# TIP: you can get this function and more from the ``more-itertools`` package.
def sliced(data: bytes, n: int) -> Iterator[bytes]:
    """
    Slices *data* into chunks of size *n*. The last slice may be smaller than
    *n*.
    """
    return takewhile(len, (data[i: i + n] for i in count(0, n)))


async def uart_terminal():
    """This is a simple "terminal" program that uses the Nordic Semiconductor
    (nRF) UART service. It reads from stdin and sends each line of data to the
    remote device. Any data received from the device is printed to stdout.
    """

    def match_nus_uuid(device: BLEDevice, adv: AdvertisementData):
        # This assumes that the device includes the UART service UUID in the
        # advertising data. This test may need to be adjusted depending on the
        # actual advertising data supplied by the device.
        if UART_SERVICE_UUID.lower() in adv.service_uuids:
            return True

        return False

    device = await BleakScanner.find_device_by_filter(match_nus_uuid)

    if device is None:
        print("no matching device found, you may need to edit match_nus_uuid().")
        sys.exit(1)

    def handle_disconnect(_: BleakClient):
        print("Device was disconnected, goodbye.")
        # cancelling all tasks effectively ends the program
        for task in asyncio.all_tasks():
            task.cancel()

    def handle_rx(_: BleakGATTCharacteristic, data: bytearray):
        process_byte_packet(data)


    async with BleakClient(device, disconnected_callback=handle_disconnect) as client:
        await client.start_notify(UART_TX_CHAR_UUID, handle_rx)

        print("Connected, start typing and press ENTER...")

        loop = asyncio.get_running_loop()
        nus = client.services.get_service(UART_SERVICE_UUID)
        rx_char = nus.get_characteristic(UART_RX_CHAR_UUID)

        while True:
            # This waits until you type a line and press ENTER.
            # A real terminal program might put stdin in raw mode so that things
            # like CTRL+C get passed to the remote device.
            data = await loop.run_in_executor(None, sys.stdin.buffer.readline)

            # data will be empty on EOF (e.g. CTRL+D on *nix)
            if not data:
                break

            # some devices, like devices running MicroPython, expect Windows
            # line endings (uncomment line below if needed)
            # data = data.replace(b"\n", b"\r\n")

            # Writing without response requires that the data can fit in a
            # single BLE packet. We can use the max_write_without_response_size
            # property to split the data into chunks that will fit.

            for s in sliced(data, rx_char.max_write_without_response_size):
                await client.write_gatt_char(rx_char, s)

            print("sent:", data)


if __name__ == "__main__":
    try:
        asyncio.run(uart_terminal())
    except asyncio.CancelledError:
        # task is cancelled on disconnect, so we ignore this error
        pass
