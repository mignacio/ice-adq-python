import asyncio
import datetime
from dataclasses import dataclass, field
import string
from BlitManager import BlitManager
from bleak import BleakClient, BleakScanner
from bleak.backends.characteristic import BleakGATTCharacteristic
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData
from collections import deque
import matplotlib.pyplot as plt
import sys

UART_SERVICE_UUID = "0000ffe0-0000-1000-8000-00805f9b34fb"
UART_RX_CHAR_UUID = "0000ffe0-0000-1000-8000-00805f9b34fb"
UART_TX_CHAR_UUID = "0000ffe1-0000-1000-8000-00805f9b34fb"
START_CHAR = bytes.fromhex("02")
END_CHAR = bytes.fromhex("03")
GROUP_SEPARATOR_CHAR = bytes.fromhex("1D")

FoundStart = False
FoundEnd = False
byte_array_buffer = bytearray()

NOTHING_FOUND = 0
FOUND_START = 1
MIDDLE_MESSAGE = 2
FOUND_END = 3
process_byte_packet_state = 0

@dataclass
class ICEMeasurement:
    label: str
    data: deque
    file: str

now = datetime.datetime.now()
filename = f"{now.strftime('%Y-%m-%d_%H-%M-%S')}.csv"

tace = ICEMeasurement('Tace', deque([(0, 0)], maxlen=24), f"Tace-{filename}.csv")
tadm = ICEMeasurement('Tadm', deque([(0, 0)], maxlen=24), f"Tadm-{filename}.csv")
tesc = ICEMeasurement('Tesc', deque([(0, 0)], maxlen=24), f"Tesc-{filename}.csv")
vbat = ICEMeasurement('Vbat', deque([(0, 0)], maxlen=24), f"Vbat-{filename}.csv")
o2 = ICEMeasurement('_O2_', deque([(0, 0)], maxlen=24), f"O2-{filename}.csv")
pace = ICEMeasurement('Pace', deque([(0, 0)], maxlen=24), f"Pace-{filename}.csv")

measurements = [tace, tadm, tesc, vbat, o2, pace]

def append_packet_to_deque(data: bytearray):
    splitted = data.split(GROUP_SEPARATOR_CHAR)
    time = int(splitted[0].decode('ascii'))
    label = splitted[1].decode('ascii')
    value = int(splitted[2].decode('ascii'))
    error = splitted[3].decode('ascii')

    for measure in measurements:
        if label == measure.label:
            measure.data.append((time,value))
            with open(measure.file, 'a') as file:
                file.write(f"{time}, {value}, {error}\n")


def find_start_and_end_chars(data: bytearray):
    start_char_index = data.find(START_CHAR)
    end_char_index = data.find(END_CHAR)
    return [start_char_index, end_char_index]


def process_byte_packet(data: bytearray):
    global process_byte_packet_state, byte_array_buffer
    if process_byte_packet_state == NOTHING_FOUND:
        # empty the buffer
        byte_array_buffer = bytearray(b'')
        start_char_index, end_char_index = find_start_and_end_chars(data)
        if start_char_index != -1:
            if start_char_index < end_char_index:
                # We found a start and end in same packet. Just print it.
                append_packet_to_deque(data[start_char_index + 1:end_char_index])
                return
            else:
                process_byte_packet_state = FOUND_START
                byte_array_buffer.extend(data[start_char_index + 1:])
        else:
            # Guess this wasn't for us
            return
    elif process_byte_packet_state == FOUND_START:
        start_char_index, end_char_index = find_start_and_end_chars(data)
        if end_char_index != -1:
            byte_array_buffer.extend(data[:end_char_index])
            append_packet_to_deque(byte_array_buffer)
            if start_char_index != -1:
                process_byte_packet_state = FOUND_START
                byte_array_buffer = data[start_char_index + 1:]
            else:
                process_byte_packet_state = NOTHING_FOUND
        else:
            process_byte_packet_state = MIDDLE_MESSAGE
            byte_array_buffer.extend(data)
    elif process_byte_packet_state == MIDDLE_MESSAGE:
        start_char_index, end_char_index = find_start_and_end_chars(data)
        if end_char_index != -1:
            byte_array_buffer.extend(data[:end_char_index])
            append_packet_to_deque(byte_array_buffer)
            if start_char_index != -1:
                process_byte_packet_state = FOUND_START
                byte_array_buffer = data[start_char_index + 1:]
            else:
                process_byte_packet_state = NOTHING_FOUND
        else:
            byte_array_buffer.extend(data)

async def uart_terminal():
    """This is a simple "terminal" program that uses the Nordic Semiconductor
    (nRF) UART service. It reads from stdin and sends each line of data to the
    remote device. Any data received from the device is printed to stdout.
    """
    now = datetime.datetime.now()
    filename = f"{now.strftime('%Y-%m-%d_%H-%M-%S')}.csv"

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
            # await asyncio.sleep(0.001)
            await loop.run_in_executor(None, sys.stdin.buffer.readline)


async def plot():
    plt.ion()
    figure, axes = plt.subplots(4,1)
    axes[0].set_title("Temperatura vs Tiempo")
    axes[0].set_xlabel("Tiempo [ms]")
    axes[0].set_ylabel("Temp. [mC]")
    axes[0].grid()

    axes[1].set_title("Tension vs tiempo")
    axes[1].set_xlabel("Tiempo [ms]")
    axes[1].set_ylabel("Tension [mV]")
    axes[1].grid()

    axes[2].set_title("Tension Bateria vs tiempo")
    axes[2].set_xlabel("Tiempo [ms]")
    axes[2].set_ylabel("Tension [mV]")
    axes[2].grid()

    tadm_line, = axes[0].plot(*zip(*tadm.data), label="Temp. Adm.")
    tesc_line, = axes[0].plot(*zip(*tesc.data), label="Temp. Esc.")
    axes[0].legend()
    axes[0].set_ylim(0, 40000)

    o2_line, = axes[1].plot(*(zip(*o2.data)), label="O2.")
    axes[1].legend()
    axes[1].set_ylim(0, 3300)

    vbat_line, = axes[2].plot(*zip(*vbat.data), label="Vbat.")
    axes[2].legend()
    axes[2].set_ylim(0, 16102)

    pace_line, = axes[3].plot(*zip(*pace.data), label="Pace.")
    axes[3].legend()
    #axes[3].set_ylim(0, 40000)

    axes3_2 = axes[3].twinx()
    tace_line, = axes3_2.plot(*zip(*tace.data), label="Temp. Ace.")
    axes3_2 = axes3_2.legend()
    #axes3_2 = axes3_2.set_ylim(0, 120)

    blitManager = BlitManager(figure.canvas, axes)

    while True:
        tace_line.set_data(*zip(*tace.data))
        tadm_line.set_data(*zip(*tadm.data))
        tesc_line.set_data(*zip(*tesc.data))

        o2_line.set_data(*zip(*o2.data))
        pace_line.set_data(*zip(*pace.data))

        vbat_line.set_data(*zip(*vbat.data))

        xlim_high = tesc.data[-1][0]
        xlim_low = xlim_high - 60000 #120 seconds
        axes[0].set_xlim(xlim_low, xlim_high)
        axes[0].autoscale_view()

        xlim_high = o2.data[-1][0]
        xlim_low = xlim_high - 60000 #120 seconds
        axes[1].set_xlim(xlim_low, xlim_high)
        axes[1].autoscale_view()

        xlim_high = vbat.data[-1][0]
        xlim_low = xlim_high - 60000 #120 seconds
        axes[2].set_xlim(xlim_low, xlim_high)
        axes[2].autoscale_view()

        xlim_high = tace.data[-1][0]
        xlim_low = xlim_high - 60000
        axes[3].set_xlim(xlim_low, xlim_high)
        #axes[3].autoscale_view

        #axes3_2.set_xlim(xlim_low, xlim_high)
        #axes3_2.autoscale_view

        blitManager.update()
        await asyncio.sleep(1)


async def main():
    t1 = loop.create_task(uart_terminal())
    t2 = loop.create_task(plot())
    await t1, t2


if __name__ == "__main__":
    try:
        loop = asyncio.new_event_loop()
        loop.run_until_complete(main())
    except asyncio.CancelledError:
        # task is cancelled on disconnect, so we ignore this error
        pass
