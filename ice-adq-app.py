"""
UART Service
-------------
An example showing how to write a simple program using the Nordic Semiconductor
(nRF) UART service.
"""

# import kivy
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

# kivy.require('1.9.0')

FoundStart = False
FoundEnd = False
byte_array_buffer = bytearray()

NOTHING_FOUND = 0
FOUND_START = 1
MIDDLE_MESSAGE = 2
FOUND_END = 3
process_byte_packet_state = 0

tace_deque = deque([(0, 0)], maxlen=30)
tadm_deque = deque([(0, 0)], maxlen=30)
tesc_deque = deque([(0, 0)], maxlen=30)

TACE_LABEL = "Tace"
TADM_LABEL = "Tadm"
TESC_LABEL = "Tesc"


def append_packet_to_deque(data: bytearray):
    splitted = data.split(GROUP_SEPARATOR_CHAR)
    time = int(splitted[0].decode('ascii'))
    value = int(splitted[2].decode('ascii'))
    label = splitted[1].decode('ascii')
    if label == TACE_LABEL:
        tace_deque.append((time, value))
    elif label == TADM_LABEL:
        tadm_deque.append((time, value))
    elif label == TESC_LABEL:
        tesc_deque.append((time, value))


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
                append_packet_to_deque(data[start_char_index + 1:end_char_index])
                return
            else:
                process_byte_packet_state = FOUND_START
                byte_array_buffer.extend(data[start_char_index+1:])
        else:
            # Guess this wasn't for us
            return
    elif process_byte_packet_state == FOUND_START:
        end_char_index = data.find(END_CHAR)
        start_char_index = data.find(START_CHAR)
        if end_char_index != -1:
            byte_array_buffer.extend(data[:end_char_index])
            append_packet_to_deque(byte_array_buffer)
            if start_char_index != -1:
                process_byte_packet_state = FOUND_START
                byte_array_buffer = data[start_char_index+1:]
            else:
                process_byte_packet_state = NOTHING_FOUND
        else:
            process_byte_packet_state = MIDDLE_MESSAGE
            byte_array_buffer.extend(data)
    elif process_byte_packet_state == MIDDLE_MESSAGE:
        end_char_index = data.find(END_CHAR)
        start_char_index = data.find(START_CHAR)
        if end_char_index != -1:
            byte_array_buffer.extend(data[:end_char_index])
            append_packet_to_deque(byte_array_buffer)
            if start_char_index != -1:
                process_byte_packet_state = FOUND_START
                byte_array_buffer = data[start_char_index+1:]
            else:
                process_byte_packet_state = NOTHING_FOUND
        else:
            byte_array_buffer.extend(data)


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
        print("Connected")
        loop = asyncio.get_running_loop()

        while True:
            #await asyncio.sleep(0.001)
            await loop.run_in_executor(None, sys.stdin.buffer.readline)


async def plot():
    plt.ion()
    figure, axes = plt.subplots()
    axes.set_xlabel("Tiempo [ms]")
    axes.set_ylabel("Temp. [mC]")
    axes.grid()
    line1, = axes.plot(*zip(*tace_deque))
    line1.set_label("Temp Ace.")
    line2, = axes.plot(*zip(*tadm_deque))
    line2.set_label("Temp Adm.")
    line3, = axes.plot(*zip(*tesc_deque), label="Temp Esc.")
    axes.legend()
    while True:
        line1.set_data(*zip(*tace_deque))
        line2.set_data(*zip(*tadm_deque))
        line3.set_data(*zip(*tesc_deque))
        axes.relim()
        axes.autoscale_view()
        figure.canvas.flush_events()
        await asyncio.sleep(1)


async def main():
    t1 = loop.create_task(uart_terminal())
    t2 = loop.create_task(plot())
    await t1, t2


if __name__ == "__main__":
    try:
        # asyncio.run(uart_terminal())
        loop = asyncio.new_event_loop()
        loop.run_until_complete(main())
    except asyncio.CancelledError:
        # task is cancelled on disconnect, so we ignore this error
        pass
