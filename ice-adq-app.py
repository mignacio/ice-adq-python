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
from kivy.uix.checkbox import CheckBox
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy_garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg

now = datetime.datetime.now()
filename = f"{now.strftime('%Y-%m-%d_%H-%M-%S')}.csv"

tace = ICEMeasurement('Tace', deque([(0, 0)], maxlen=120), f"Tace-{filename}.csv", True)
tadm = ICEMeasurement('Tadm', deque([(0, 0)], maxlen=120), f"Tadm-{filename}.csv", True)
tesc = ICEMeasurement('Tesc', deque([(0, 0)], maxlen=120), f"Tesc-{filename}.csv", True)
vbat = ICEMeasurement('Vbat', deque([(0, 0)], maxlen=120), f"Vbat-{filename}.csv", True)
o2 = ICEMeasurement('_O2_', deque([(0, 0)], maxlen=120), f"O2-{filename}.csv", True)
pace = ICEMeasurement('Pace', deque([(0, 0)], maxlen=120), f"Pace-{filename}.csv", True)
rpm = ICEMeasurement('RPM', deque([(0, 0)], maxlen=120), f"Pace-{filename}.csv", True)

measurements = [tace, tadm, tesc, vbat, o2, pace, rpm]

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

        vbat_v_t.set_title("Tension Bateria vs tiempo")
        vbat_v_t.set_xlabel("Tiempo [ms]")
        vbat_v_t.set_ylabel("Tension [mV]")
        vbat_v_t.grid()

        o2_v_t.set_title("Tension vs tiempo")
        o2_v_t.set_xlabel("Tiempo [ms]")
        o2_v_t.set_ylabel("Tension [mV]")
        o2_v_t.grid()

        tadm_line, = gas_v_t.plot(*zip(*tadm.data), label="Temp. Adm.")
        tesc_line, = gas_v_t.plot(*zip(*tesc.data), label="Temp. Esc.")
        gas_v_t.legend(loc='upper left')
        gas_v_t.set_ylim(0, 40000)

        vbat_line, = vbat_v_t.plot(*(zip(*o2.data)), label="Vbat.")
        vbat_v_t.legend(loc='upper left')
        vbat_v_t.set_ylim(0, 16102)

        o2_line, = o2_v_t.plot(*zip(*vbat.data), label="O2.")
        o2_v_t.legend(loc='upper left')
        o2_v_t.set_ylim(0, 3300)

        rpm_v_t = o2_v_t.twinx()
        rpm_line, = rpm_v_t.plot(*zip(*rpm.data), label="RPM.")
        rpm_v_t.legend(loc='upper right')

        tace_line, = ace_v_t.plot(*zip(*pace.data), label="Temp. Ace.")
        ace_v_t.legend(loc='upper left')
        ace_v_t.set_ylim(0, 40000)
        ace_v_t.grid()

        pace_v_t = ace_v_t.twinx()
        pace_line, = pace_v_t.plot(*zip(*tace.data), label="Pres. Ace.")
        pace_v_t.legend(loc='upper right')

        #blitManager = BlitManager(fig.canvas, axes)

        while True:
            tace_line.set_data(*zip(*tace.data))
            tadm_line.set_data(*zip(*tadm.data))
            tesc_line.set_data(*zip(*tesc.data))
            o2_line.set_data(*zip(*o2.data))
            rpm_line.set_data(*zip(*rpm.data))
            pace_line.set_data(*zip(*pace.data))
            vbat_line.set_data(*zip(*vbat.data))
            
            tace_line.set_visible(tace.visible)
            tadm_line.set_visible(tadm.visible)
            tesc_line.set_visible(tesc.visible)
            o2_line.set_visible(o2.visible)
            rpm_line.set_visible(rpm.visible)
            pace_line.set_visible(pace.visible)
            vbat_line.set_visible(vbat.visible)

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
        tabbed_panel = TabbedPanel(do_default_tab=False)
        graficas_tab = TabbedPanelItem(text='Graficas')
        config_tab = TabbedPanelItem(text='Config')
        tabbed_panel.add_widget(graficas_tab)
        tabbed_panel.add_widget(config_tab)

        top_box = BoxLayout(orientation = 'vertical', spacing=10)
        box = BoxLayout( orientation = 'horizontal', spacing=8, size_hint=(1, 0.05))

        self.connect_btn = Button(text="Connect", size_hint=(0.125, 1))
        self.show_tadm_btn = Button(text="Tadm", size_hint=(0.125, 1))
        self.show_tadm_btn.bind(on_press=self.on_tadm_active)
        self.show_tesc_btn = Button(text="Tesc", size_hint=(0.125, 1))
        self.show_tesc_btn.bind(on_press=self.on_tesc_active)
        self.show_tace_btn = Button(text="Tace", size_hint=(0.125, 1))
        self.show_tace_btn.bind(on_press=self.on_tace_active)
        self.show_pace_btn = Button(text="Pace", size_hint=(0.125, 1))
        self.show_pace_btn.bind(on_press=self.on_pace_active)
        self.show_vbat_btn = Button(text="Vbat", size_hint=(0.125, 1))
        self.show_vbat_btn.bind(on_press=self.on_vbat_active)
        self.show_o2_btn = Button(text="O2", size_hint=(0.125, 1))
        self.show_o2_btn.bind(on_press=self.on_o2_active)
        self.show_rpm_btn = Button(text="RPM", size_hint=(0.125, 1))
        self.show_rpm_btn.bind(on_press=self.on_rpm_active)

        box.add_widget(self.connect_btn)
        box.add_widget(self.show_tadm_btn)
        box.add_widget(self.show_tesc_btn)
        box.add_widget(self.show_tace_btn)
        box.add_widget(self.show_pace_btn)
        box.add_widget(self.show_vbat_btn)
        box.add_widget(self.show_o2_btn)
        box.add_widget(self.show_rpm_btn)
        self.connect_btn.bind(on_press=self.ble_connect_callback)

        box2 = BoxLayout(orientation = 'vertical', spacing=10, size_hint=(1, 0.95))
        self.fig, self.axes = plt.subplots(2,2)
        plt.ion()
        self.canvas = FigureCanvasKivyAgg(self.fig, size_hint=(1, 0.95))
        box2.add_widget(self.canvas)

        try:
            asyncio.create_task(self.plot())
        except asyncio.CancelledError:
            pass

        top_box.add_widget(box)
        top_box.add_widget(box2)
        graficas_tab.add_widget(top_box)
        return tabbed_panel


    def ble_connect_callback(self, instance):
        try:
            asyncio.create_task(uart_terminal(measurements))
        except asyncio.CancelledError:
            pass

    def on_tadm_active(self, instance):
        tadm.visible = not tadm.visible

    def on_tesc_active(self, instance):
        tesc.visible = not tesc.visible

    def on_tace_active(self, instance):
        tace.visible = not tace.visible

    def on_pace_active(self, instance):
        pace.visible = not pace.visible

    def on_vbat_active(self, instance):
        vbat.visible = not vbat.visible

    def on_o2_active(self, instance):
        o2.visible = not o2.visible

    def on_rpm_active(self, instance):
        rpm.visible = not rpm.visible

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.run_until_complete(MainApp().async_run())
