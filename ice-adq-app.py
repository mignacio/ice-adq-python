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
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy_garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg

now = datetime.datetime.now()
filename = f"{now.strftime('%Y-%m-%d_%H-%M-%S')}.csv"

tace = ICEMeasurement('Tace', deque([(0, 0)], maxlen=120), f"Tace-{filename}.csv")
tadm = ICEMeasurement('Tadm', deque([(0, 0)], maxlen=120), f"Tadm-{filename}.csv")
tesc = ICEMeasurement('Tesc', deque([(0, 0)], maxlen=120), f"Tesc-{filename}.csv")
vbat = ICEMeasurement('Vbat', deque([(0, 0)], maxlen=120), f"Vbat-{filename}.csv")
o2 = ICEMeasurement('_O2_', deque([(0, 0)], maxlen=120), f"O2-{filename}.csv")
pace = ICEMeasurement('Pace', deque([(0, 0)], maxlen=120), f"Pace-{filename}.csv")

measurements = [tace, tadm, tesc, vbat, o2, pace]

class MainApp(App):

    async def plot(self):

        gas_v_t = self.axes[0][0]
        vbat_v_t = self.axes[1][0]
        o2_v_t = self.axes[0][1]
        ace_v_t = self.axes[1][1]

        gas_v_t.set_title("Temperatura vs Tiempo")
        gas_v_t.set_xlabel("Tiempo [ms]")
        gas_v_t.set_ylabel("Temp. [mC]")
        gas_v_t.grid()

        vbat_v_t.set_title("Tension vs tiempo")
        vbat_v_t.set_xlabel("Tiempo [ms]")
        vbat_v_t.set_ylabel("Tension [mV]")
        vbat_v_t.grid()

        o2_v_t.set_title("Tension Bateria vs tiempo")
        o2_v_t.set_xlabel("Tiempo [ms]")
        o2_v_t.set_ylabel("Tension [mV]")
        o2_v_t.grid()

        tadm_line, = gas_v_t.plot(*zip(*tadm.data), label="Temp. Adm.")
        tesc_line, = gas_v_t.plot(*zip(*tesc.data), label="Temp. Esc.")
        gas_v_t.legend()
        gas_v_t.set_ylim(0, 40000)

        o2_line, = vbat_v_t.plot(*(zip(*o2.data)), label="O2.")
        vbat_v_t.legend()
        vbat_v_t.set_ylim(0, 3300)

        vbat_line, = o2_v_t.plot(*zip(*vbat.data), label="Vbat.")
        o2_v_t.legend()
        o2_v_t.set_ylim(0, 16102)

        pace_line, = ace_v_t.plot(*zip(*pace.data), label="Pace.")
        ace_v_t.legend()
        #axes[3].set_ylim(0, 40000)

        axes3_2 = ace_v_t.twinx()
        tace_line, = axes3_2.plot(*zip(*tace.data), label="Temp. Ace.")
        axes3_2 = axes3_2.legend()
        #axes3_2 = axes3_2.set_ylim(0, 120)

        #blitManager = BlitManager(fig.canvas, axes)

        while True:
            tace_line.set_data(*zip(*tace.data))
            tadm_line.set_data(*zip(*tadm.data))
            tesc_line.set_data(*zip(*tesc.data))

            o2_line.set_data(*zip(*o2.data))
            pace_line.set_data(*zip(*pace.data))

            vbat_line.set_data(*zip(*vbat.data))

            xlim_high = tesc.data[-1][0]
            xlim_low = xlim_high - 60000 #120 seconds
            gas_v_t.set_xlim(xlim_low, xlim_high)
            gas_v_t.autoscale_view()

            xlim_high = o2.data[-1][0]
            xlim_low = xlim_high - 60000 #120 seconds
            vbat_v_t.set_xlim(xlim_low, xlim_high)
            vbat_v_t.autoscale_view()

            xlim_high = vbat.data[-1][0]
            xlim_low = xlim_high - 60000 #120 seconds
            o2_v_t.set_xlim(xlim_low, xlim_high)
            o2_v_t.autoscale_view()

            xlim_high = tace.data[-1][0]
            xlim_low = xlim_high - 60000
            ace_v_t.set_xlim(xlim_low, xlim_high)
            #axes[3].autoscale_view

            #axes3_2.set_xlim(xlim_low, xlim_high)
            #axes3_2.autoscale_view

            #blitManager.update()
            self.canvas.draw()
            await asyncio.sleep(1)

    def build(self):
        box = BoxLayout( orientation = 'vertical', spacing=10)

        self.connect_btn = Button
        self.connect_btn = Button(text="Connect", size_hint=(1, 0.05))
        box.add_widget(self.connect_btn)
        self.connect_btn.bind(on_press=self.ble_connect_callback)

        self.fig, self.axes = plt.subplots(2,2)
        plt.ion()
        self.canvas = FigureCanvasKivyAgg(self.fig, size_hint=(1, 0.95))
        box.add_widget(self.canvas)

        try:
            asyncio.create_task(self.plot())
        except asyncio.CancelledError:
            pass
        return box
    
    def ble_connect_callback(self, instance):
        try:
            asyncio.create_task(uart_terminal(measurements))
        except asyncio.CancelledError:
            pass

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.run_until_complete(MainApp().async_run())
