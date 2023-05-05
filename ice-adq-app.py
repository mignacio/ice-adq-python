#Generic imports
import asyncio
from collections import deque
import datetime
from ICEMeasurement import ICEMeasurement
from UARTTerminal import uart_terminal
#Plot Imports
import matplotlib.pyplot as plt
from BlitManager import BlitManager
# Kivy imports
from kivy.lang import Builder
from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy_garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg

now = datetime.datetime.now()
filename = f"{now.strftime('%Y-%m-%d_%H-%M-%S')}.csv"

tace = ICEMeasurement('Tace', deque([(0, 0)], maxlen=24), f"Tace-{filename}.csv")
tadm = ICEMeasurement('Tadm', deque([(0, 0)], maxlen=24), f"Tadm-{filename}.csv")
tesc = ICEMeasurement('Tesc', deque([(0, 0)], maxlen=24), f"Tesc-{filename}.csv")
vbat = ICEMeasurement('Vbat', deque([(0, 0)], maxlen=24), f"Vbat-{filename}.csv")
o2 = ICEMeasurement('_O2_', deque([(0, 0)], maxlen=24), f"O2-{filename}.csv")
pace = ICEMeasurement('Pace', deque([(0, 0)], maxlen=24), f"Pace-{filename}.csv")

measurements = [tace, tadm, tesc, vbat, o2, pace]


async def plot(fig: plt.figure, axes):

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

    blitManager = BlitManager(fig.canvas, axes)

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


class IceAppLayout(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        fig, axes = plt.subplots(4,1)
        
        box = self.ids.box
        box.add_widget(FigureCanvasKivyAgg(fig))

        try:
            asyncio.create_task(plot(fig, axes))
        except asyncio.CancelledError:
            pass

    def ble_connect_callback(self):
        try:
            asyncio.create_task(uart_terminal(measurements))
        except asyncio.CancelledError:
            pass

class MainApp(App):
    def build(self):
        Builder.load_file('IceAppLayout.kv')
        return IceAppLayout()

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.run_until_complete(MainApp().async_run())
