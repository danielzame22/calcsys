# screens/nav.py
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.graphics import Color, Rectangle, Line
from theme import *


class NavButton(BoxLayout):
    def __init__(self, icon, label_text, name, on_press_cb, **kw):
        super().__init__(orientation='vertical', spacing=2, padding=[0, 6, 0, 6], **kw)
        self.name = name
        self.on_press_cb = on_press_cb
        self._active = False

        self.icon_lbl = Label(
            text=icon, font_size='20sp',
            color=TEXT3, size_hint_y=None, height=26,
            halign='center'
        )
        self.text_lbl = Label(
            text=label_text.upper(), font_size='8sp',
            color=TEXT3, size_hint_y=None, height=14,
            halign='center', font_name=FONT_MONO
        )
        self.add_widget(self.icon_lbl)
        self.add_widget(self.text_lbl)

        self.bind(on_touch_down=self._touch)

    def _touch(self, *a):
        pass  # handled by parent

    def set_active(self, v):
        self._active = v
        c = ACCENT if v else TEXT3
        self.icon_lbl.color = c
        self.text_lbl.color = c


class NavBar(BoxLayout):
    def __init__(self, switch_cb, **kw):
        super().__init__(
            orientation='horizontal',
            size_hint_y=None, height=56,
            **kw
        )
        self.switch_cb = switch_cb
        self._buttons = {}

        with self.canvas.before:
            Color(*BG)
            self._bg = Rectangle(pos=self.pos, size=self.size)
            Color(*BORDER)
            self._line = Line(points=[self.x, self.top, self.right, self.top], width=1)
        self.bind(pos=self._update_bg, size=self._update_bg)

        tabs = [
            ('⌗', 'solver', 'solver'),
            ('⊞', 'sudoku', 'sudoku'),
        ]
        for icon, label, name in tabs:
            btn = NavButton(icon, label, name, switch_cb, size_hint_x=1)
            self._buttons[name] = btn
            self.add_widget(btn)

        self.set_active('solver')

        # touch handling on the bar itself
        self.bind(on_touch_down=self._on_touch)

    def _update_bg(self, *a):
        self._bg.pos = self.pos
        self._bg.size = self.size
        self._line.points = [self.x, self.top, self.right, self.top]

    def _on_touch(self, instance, touch):
        if not self.collide_point(*touch.pos):
            return False
        for name, btn in self._buttons.items():
            if btn.collide_point(*touch.pos):
                self.switch_cb(name)
                return True
        return False

    def set_active(self, name):
        for n, btn in self._buttons.items():
            btn.set_active(n == name)
