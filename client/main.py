import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.core.window import Window
from stream import StreamReceiver
import os

Window.clearcolor = (0.07, 0.07, 0.07, 1)

class BTDSClient(App):
    def build(self):
        self.title = 'BetterDisplay (BTDS)'
        
        # Try to set icon
        icon_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'assets', 'icon.jpg'))
        if os.path.exists(icon_path):
            self.icon = icon_path

        self.root = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        self.header = Label(
            text='[b][color=00FFCC]BETTERDISPLAY[/color][/b]',
            markup=True,
            font_size='32sp',
            size_hint=(1, 0.1)
        )
        self.root.add_widget(self.header)
        
        self.status_label = Label(
            text='Status: Waiting for connection...',
            color=(0.7, 0.7, 0.7, 1),
            font_size='18sp',
            size_hint=(1, 0.1)
        )
        self.root.add_widget(self.status_label)
        
        ip_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.1), spacing=10)
        ip_label = Label(text='Target IP:', size_hint=(0.3, 1), color=(1,1,1,1))
        self.ip_input = TextInput(
            text='127.0.0.1', 
            multiline=False, 
            background_color=(0.12, 0.12, 0.12, 1),
            foreground_color=(1, 1, 1, 1),
            size_hint=(0.7, 1)
        )
        ip_layout.add_widget(ip_label)
        ip_layout.add_widget(self.ip_input)
        self.root.add_widget(ip_layout)
        
        btn_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.15), spacing=15)
        self.btn_connect = Button(
            text='Connect',
            background_normal='',
            background_color=(0.12, 0.12, 0.12, 1),
            color=(0, 1, 0.8, 1),
            bold=True
        )
        self.btn_connect.bind(on_press=self.toggle_connection)
        btn_layout.add_widget(self.btn_connect)
        self.root.add_widget(btn_layout)
        
        self.video_display = Image(allow_stretch=True, keep_ratio=True, size_hint=(1, 0.55))
        self.root.add_widget(self.video_display)
        
        self.receiver = None
        
        return self.root

    def toggle_connection(self, instance):
        if self.receiver and self.receiver.is_running:
            self.receiver.stop()
        else:
            ip = self.ip_input.text
            port = 5000
            self.status_label.text = f'Connecting to {ip}:{port}...'
            self.btn_connect.text = 'Disconnect'
            
            self.receiver = StreamReceiver(
                ip=ip, 
                port=port, 
                image_widget=self.video_display,
                on_connect=self.on_connected,
                on_disconnect=self.on_disconnected
            )
            self.receiver.start()
            
    def on_connected(self):
        self.status_label.text = '[color=00FF00]Status: Connected[/color]'
        self.status_label.markup = True
        
    def on_disconnected(self):
        self.status_label.text = 'Status: Disconnected'
        self.status_label.markup = False
        self.btn_connect.text = 'Connect'
        self.video_display.texture = None

if __name__ == '__main__':
    BTDSClient().run()
