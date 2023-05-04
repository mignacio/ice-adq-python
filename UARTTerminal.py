import asyncio
from ICEMeasurement import ICEMeasurement
from bleak import BleakClient, BleakScanner
from bleak.backends.characteristic import BleakGATTCharacteristic
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData
import sys

START_CHAR = bytes.fromhex("02")
END_CHAR = bytes.fromhex("03")
GROUP_SEPARATOR_CHAR = bytes.fromhex("1D")

process_byte_packet_state = 0
byte_array_buffer = bytearray()
NOTHING_FOUND = 0
FOUND_START = 1
MIDDLE_MESSAGE = 2

UART_SERVICE_UUID = "0000ffe0-0000-1000-8000-00805f9b34fb"
UART_RX_CHAR_UUID = "0000ffe0-0000-1000-8000-00805f9b34fb"
UART_TX_CHAR_UUID = "0000ffe1-0000-1000-8000-00805f9b34fb"

async def uart_terminal(measurements: ICEMeasurement):

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