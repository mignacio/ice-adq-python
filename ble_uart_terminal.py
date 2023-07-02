import asyncio
import datetime
from bleak import BleakClient, BleakScanner
from bleak.backends.characteristic import BleakGATTCharacteristic
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData
import sys

from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput

UART_SERVICE_UUID = "0000ffe0-0000-1000-8000-00805f9b34fb"
UART_RX_CHAR_UUID = "0000ffe0-0000-1000-8000-00805f9b34fb"
UART_TX_CHAR_UUID = "0000ffe1-0000-1000-8000-00805f9b34fb"

async def ble_uart_terminal():
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
        print(data)

    async with BleakClient(device, disconnected_callback=handle_disconnect) as client:
        await client.start_notify(UART_TX_CHAR_UUID, handle_rx)
        print("Connected")
        loop = asyncio.get_running_loop()

        while True:
            # await asyncio.sleep(0.001)
            await loop.run_in_executor(None, sys.stdin.buffer.readline)

class SayHello(App):

    def build(self):
        self.window = GridLayout()
        self.window.cols = 1
        self.greeting = Label(text="ICE ADQ APP")
        self.window.add_widget(self.greeting)
        self.button = Button(text="Connect")
        self.button.bind(on_press=self.ble_connect_callback)
        self.window.add_widget(self.button)
        return self.window

    def ble_connect_callback(self, instance):
        try:
            asyncio.create_task(ble_uart_terminal())
        except asyncio.CancelledError:
            pass


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.run_until_complete(SayHello().async_run())
