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
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.checkbox import CheckBox
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy_garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg

now = datetime.datetime.now()
filename = f"{now.strftime('%Y-%m-%d_%H-%M-%S')}.csv"

tace    = ICEMeasurement('Tace', deque([(0, 0)], maxlen=120), f"Tace-{filename}.csv", True, False, 33000)
tadm    = ICEMeasurement('Tadm', deque([(0, 0)], maxlen=120), f"Tadm-{filename}.csv", True, False, 18000)
tesc    = ICEMeasurement('Tesc', deque([(0, 0)], maxlen=120), f"Tesc-{filename}.csv", True, False, 33000)
vbat    = ICEMeasurement('Vbat', deque([(0, 0)], maxlen=120), f"Vbat-{filename}.csv", True, False, 15000)
o2      = ICEMeasurement('_O2_', deque([(0, 0)], maxlen=120), f"O2-{filename}.csv", True, False, 33000)
pace    = ICEMeasurement('Pace', deque([(0, 0)], maxlen=120), f"Pace-{filename}.csv", True, False, 9000)
rpm     = ICEMeasurement('RPM', deque([(0, 0)], maxlen=120), f"Pace-{filename}.csv", True, False, 33000)

measurements = [tace, tadm, tesc, vbat, o2, pace, rpm]
class MainApp(App):

    xlim_global = 60000

    async def alarms(self):
        alarm_color = (1,0.1,0.1,1)
        def_color = (1,1,1,1)

        while True:
            if tace.alarm == True:
                self.ace_label.color = alarm_color
            else:
                self.ace_label.color = def_color

            if tadm.alarm == True:
                self.adm_label.color = alarm_color
            else:
                self.adm_label.color = def_color

            if tesc.alarm == True:
                self.esc_label.color = alarm_color
            else:
                self.esc_label.color = def_color

            if vbat.alarm == True:
                self.vbat_label.color = alarm_color
            else:
                self.vbat_label.color = def_color

            if o2.alarm == True:
                self.o2_label.color = alarm_color
            else:
                self.o2_label.color = def_color

            if pace.alarm == True:
                self.pace_label.color = alarm_color
            else:
                self.pace_label.color = def_color

            if rpm.alarm == True:
                self.rpm_label.color = alarm_color
            else:
                self.rpm_label.color = def_color

            await asyncio.sleep(1)

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
        gas_v_t.set_ylim(0, 4000)

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
        ace_v_t.set_ylim(0, 4000)
        ace_v_t.grid()

        pace_v_t = ace_v_t.twinx()
        pace_v_t.set_ylim(0, 15000)
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
            xlim_low = xlim_high - self.xlim_global
            gas_v_t.set_xlim(xlim_low, xlim_high)
            gas_v_t.autoscale_view()

            xlim_high = o2.data[-1][0]
            xlim_low = xlim_high - self.xlim_global
            vbat_v_t.set_xlim(xlim_low, xlim_high)
            vbat_v_t.autoscale_view()

            xlim_high = vbat.data[-1][0]
            xlim_low = xlim_high - self.xlim_global
            o2_v_t.set_xlim(xlim_low, xlim_high)
            o2_v_t.autoscale_view()

            xlim_high = tace.data[-1][0]
            xlim_low = xlim_high - self.xlim_global
            ace_v_t.set_xlim(xlim_low, xlim_high)
            ace_v_t.autoscale_view()
            pace_v_t.autoscale_view()

            #blitManager.update()
            self.canvas.draw()
            await asyncio.sleep(1)

    def build(self):

        def make_minus_btn():
            return Button(text='-', size_hint=(0.250,1))

        def make_plus_btn():
            return Button(text='+', size_hint=(0.250,1))

        config_tab = TabbedPanelItem(text='Config')
        config_box = BoxLayout(orientation = 'vertical', spacing=5)
        tesc_box = BoxLayout(orientation = 'horizontal', spacing=5, size_hint=(1, 0.05))
        self.tesc_minus_btn = make_minus_btn()
        self.tesc_alarm_label = Label(text='48')
        self.tesc_plus_btn = make_plus_btn()
        tesc_box.add_widget(Label(text='Alarma T. Esc.'))
        tesc_box.add_widget(self.tesc_minus_btn)
        tesc_box.add_widget(self.tesc_alarm_label)
        tesc_box.add_widget(self.tesc_plus_btn)
        config_box.add_widget(tesc_box)

        tadm_box = BoxLayout(orientation = 'horizontal', spacing=5, size_hint=(1, 0.05))
        self.tadm_minus_btn = make_minus_btn()
        self.tadm_alarm_label = Label(text='40')
        self.tadm_plus_btn = make_plus_btn()
        tadm_box.add_widget(Label(text="Alarma T. Adm."))
        tadm_box.add_widget(self.tadm_minus_btn)
        tadm_box.add_widget(self.tadm_alarm_label)
        tadm_box.add_widget(self.tadm_plus_btn)
        config_box.add_widget(tadm_box)

        tace_box = BoxLayout(orientation = 'horizontal', spacing=5, size_hint=(1, 0.05))
        self.tace_minus_btn = make_minus_btn()
        self.tace_alarm_label = Label(text='48')
        self.tace_plus_btn = make_plus_btn()
        tace_box.add_widget(Label(text="Alarma T. Ace."))
        tace_box.add_widget(self.tace_minus_btn)
        tace_box.add_widget(self.tace_alarm_label)
        tace_box.add_widget(self.tace_plus_btn)
        config_box.add_widget(tace_box)

        pace_box = BoxLayout(orientation = 'horizontal', spacing=5, size_hint=(1, 0.05))
        self.pace_minus_btn = make_minus_btn()
        self.pace_alarm_label = Label(text='48')
        self.pace_plus_btn = make_plus_btn()
        pace_box.add_widget(Label(text="Alarma P. Ace."))
        pace_box.add_widget(self.pace_minus_btn)
        pace_box.add_widget(self.pace_alarm_label)
        pace_box.add_widget(self.pace_plus_btn)
        config_box.add_widget(pace_box)

        o2_box = BoxLayout(orientation = 'horizontal', spacing=5, size_hint=(1, 0.05))
        self.o2_minus_btn = make_minus_btn()
        self.o2_alarm_label = Label(text='48')
        self.o2_plus_btn = make_plus_btn()
        o2_box.add_widget(Label(text="Alarma O2."))
        o2_box.add_widget(self.o2_minus_btn)
        o2_box.add_widget(self.o2_alarm_label)
        o2_box.add_widget(self.o2_plus_btn)
        config_box.add_widget(o2_box)

        rpm_box = BoxLayout(orientation = 'horizontal', spacing=5, size_hint=(1, 0.05))
        self.rpm_minus_btn = make_minus_btn()
        self.rpm_alarm_label = Label(text='48')
        self.rpm_plus_btn = make_plus_btn()
        rpm_box.add_widget(Label(text="Alarma RPM."))
        rpm_box.add_widget(self.rpm_minus_btn)
        rpm_box.add_widget(self.rpm_alarm_label)
        rpm_box.add_widget(self.rpm_plus_btn)
        config_box.add_widget(rpm_box)

        vbat_box = BoxLayout(orientation = 'horizontal', spacing=5, size_hint=(1, 0.05))
        self.vbat_minus_btn = make_minus_btn()
        self.vbat_alarm_label = Label(text='48')
        self.vbat_plus_btn = make_plus_btn()
        vbat_box.add_widget(Label(text="Alarma V. Bat."))
        vbat_box.add_widget(self.vbat_minus_btn)
        vbat_box.add_widget(self.vbat_alarm_label)
        vbat_box.add_widget(self.vbat_plus_btn)
        config_box.add_widget(vbat_box)

        config_tab.add_widget(config_box)

        graficas_tab = TabbedPanelItem(text='Graficas')
        top_box = BoxLayout(orientation = 'vertical', spacing=10)
        btn_box = BoxLayout(orientation = 'horizontal', spacing=5, size_hint=(1, 0.05))
        lbl_box = BoxLayout(orientation = 'horizontal', spacing=5, size_hint=(1, 0.05))

        self.adm_label = Label(text="TAdm")
        self.esc_label = Label(text="TEsc")
        self.ace_label = Label(text="TAce")
        self.pace_label = Label(text="Pace")
        self.vbat_label = Label(text="VBat")
        self.o2_label = Label(text="O2")
        self.rpm_label = Label(text="RPM")

        lbl_box.add_widget(self.adm_label)
        lbl_box.add_widget(self.esc_label)
        lbl_box.add_widget(self.ace_label)
        lbl_box.add_widget(self.pace_label)
        lbl_box.add_widget(self.vbat_label)
        lbl_box.add_widget(self.o2_label)
        lbl_box.add_widget(self.rpm_label)

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

        btn2_box = BoxLayout( orientation = 'horizontal', spacing=5, size_hint=(1, 0.05))
        self.sec10_btn = Button(text="10 sec.", size_hint=(0.25, 1))
        self.sec10_btn.bind(on_press=self.on_sec10_callback)
        self.sec30_btn = Button(text="30 sec.", size_hint=(0.25, 1))
        self.sec30_btn.bind(on_press=self.on_sec30_callback)
        self.sec60_btn = Button(text="60 sec.", size_hint=(0.25, 1))
        self.sec60_btn.bind(on_press=self.on_sec_60_callback)
        self.sec120_btn = Button(text="120 sec.", size_hint=(0.25, 1))
        self.sec120_btn.bind(on_press=self.on_sec120_callback)

        btn2_box.add_widget(self.sec10_btn)
        btn2_box.add_widget(self.sec30_btn)
        btn2_box.add_widget(self.sec60_btn)
        btn2_box.add_widget(self.sec120_btn)

        btn_box.add_widget(self.connect_btn)
        btn_box.add_widget(self.show_tadm_btn)
        btn_box.add_widget(self.show_tesc_btn)
        btn_box.add_widget(self.show_tace_btn)
        btn_box.add_widget(self.show_pace_btn)
        btn_box.add_widget(self.show_vbat_btn)
        btn_box.add_widget(self.show_o2_btn)
        btn_box.add_widget(self.show_rpm_btn)
        self.connect_btn.bind(on_press=self.ble_connect_callback)

        plot_box = BoxLayout(orientation = 'vertical', spacing=10, size_hint=(1, 0.95))
        self.fig, self.axes = plt.subplots(2,2)
        plt.ion()
        self.canvas = FigureCanvasKivyAgg(self.fig, size_hint=(1, 0.95))
        plot_box.add_widget(self.canvas)

        try:
            asyncio.create_task(self.plot())
        except asyncio.CancelledError:
            pass

        try:
            asyncio.create_task(self.alarms())
        except asyncio.CancelledError:
            pass

        top_box.add_widget(btn_box)
        top_box.add_widget(btn2_box)
        top_box.add_widget(lbl_box)
        top_box.add_widget(plot_box)
        graficas_tab.add_widget(top_box)

        tabbed_panel = TabbedPanel(do_default_tab=False)
        log_tab = TabbedPanelItem(text='Log')
        tabbed_panel.add_widget(graficas_tab)
        tabbed_panel.add_widget(config_tab)
        tabbed_panel.add_widget(log_tab)
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

    def on_sec10_callback(self, instance):
        self.xlim_global = 10000

    def on_sec30_callback(self, instance):
        self.xlim_global = 30000

    def on_sec_60_callback(self, instance):
        self.xlim_global = 60000
        self.rpm_label.color =(1,1,1,1)

    def on_sec120_callback(self, instance):
        self.xlim_global = 120000
        self.rpm_label.color = (1,0,0,1)

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.run_until_complete(MainApp().async_run())
