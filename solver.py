# screens/solver.py
import threading

from kivy.uix.screen import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle, RoundedRectangle, Line

import storage
from math_engine import resolver as math_resolver
from theme import *


QUICK = [
    ('cuadrática', 'Resuelve: 2x² + 3x - 5 = 0'),
    ('∫ integral',  'Calcula la integral de sen(x) dx'),
    ('derivada',   'Deriva f(x) = x³ - 4x + 2'),
    ('factorizar', 'Factoriza: x² - 9'),
    ('sistema',    'Sistema de ecuaciones: 2x + y = 7, x - y = 1'),
    ('límite',     'Límite cuando x→∞ de (1 + 1/x)^x'),
    ('logaritmo',  'Logaritmo: log₂(128)'),
    ('tabla',      'Tabla de valores para f(x) = x² entre -3 y 3'),
]


def _bg(widget, color):
    with widget.canvas.before:
        Color(*color)
        rect = Rectangle(pos=widget.pos, size=widget.size)
    widget.bind(pos=lambda *a: setattr(rect, 'pos', widget.pos),
                size=lambda *a: setattr(rect, 'size', widget.size))


def _make_label(text, font_size='12sp', color=None, halign='left', bold=False):
    lbl = Label(
        text=text, font_size=font_size,
        color=color or TEXT,
        halign=halign, valign='top',
        font_name=FONT_MONO,
        bold=bold,
        size_hint_y=None,
        markup=True,
    )
    lbl.bind(texture_size=lambda i, v: setattr(i, 'height', v[1]))
    lbl.bind(width=lambda i, v: setattr(i, 'text_size', (v, None)))
    return lbl


class SectionLabel(Label):
    def __init__(self, text, **kw):
        super().__init__(
            text=f'// {text.upper()}',
            font_size='9sp', color=TEXT3,
            halign='left', font_name=FONT_MONO,
            size_hint_y=None, height=22,
            **kw
        )
        self.bind(width=lambda i, v: setattr(i, 'text_size', (v, None)))


class CardBox(BoxLayout):
    """BoxLayout with dark card background."""
    def __init__(self, **kw):
        super().__init__(**kw)
        with self.canvas.before:
            Color(*BG2)
            self._rect = Rectangle(pos=self.pos, size=self.size)
            Color(*BORDER2)
            self._line = Line(rectangle=(*self.pos, *self.size), width=1)
        self.bind(pos=self._upd, size=self._upd)

    def _upd(self, *a):
        self._rect.pos = self.pos; self._rect.size = self.size
        self._line.rectangle = (*self.pos, *self.size)


class TerminalInput(TextInput):
    def __init__(self, **kw):
        super().__init__(
            background_color=(0, 0, 0, 0),
            foreground_color=TEXT,
            cursor_color=ACCENT,
            hint_text_color=TEXT3,
            font_name=FONT_MONO,
            font_size='13sp',
            multiline=True,
            **kw
        )


class HistoryItem(BoxLayout):
    def __init__(self, q, a, **kw):
        super().__init__(orientation='vertical', size_hint_y=None, **kw)
        with self.canvas.before:
            Color(*BG3)
            self._bg = Rectangle(pos=self.pos, size=self.size)
            Color(*BORDER)
            self._border = Line(rectangle=(*self.pos, *self.size), width=1)
        self.bind(pos=self._upd, size=self._upd)

        q_lbl = _make_label(f'[color=#888888]› {q[:60]}{"…" if len(q)>60 else ""}[/color]',
                            font_size='11sp', color=TEXT2)
        a_lbl = _make_label(a[:200] + ('…' if len(a) > 200 else ''),
                            font_size='11sp', color=TEXT)

        self.add_widget(q_lbl)
        self.add_widget(a_lbl)
        self.bind(children=self._fix_height)

    def _upd(self, *a):
        self._bg.pos = self.pos; self._bg.size = self.size
        self._border.rectangle = (*self.pos, *self.size)

    def _fix_height(self, *a):
        Clock.schedule_once(lambda dt: setattr(self, 'height',
            sum(c.height for c in self.children) + 16), 0)


class SolverScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self._build()

    def _build(self):
        root = BoxLayout(orientation='vertical', padding=12, spacing=8)
        _bg(root, BG)

        sv = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        inner = BoxLayout(orientation='vertical', spacing=10, size_hint_y=None, padding=[0, 0, 0, 16])
        inner.bind(minimum_height=inner.setter('height'))

        # ── Input area ──────────────────────────────
        inner.add_widget(SectionLabel('solver'))

        input_card = CardBox(orientation='horizontal', size_hint_y=None, height=90, padding=8)
        prompt_lbl = Label(text='›', font_size='14sp', color=ACCENT,
                           size_hint_x=None, width=16, font_name=FONT_MONO)
        self.text_input = TerminalInput(
            hint_text='Escribe una ecuación o problema…\nEj: integral de x^2 dx\nEj: 2x + 5 = 13',
        )
        input_card.add_widget(prompt_lbl)
        input_card.add_widget(self.text_input)
        inner.add_widget(input_card)

        # ── Buttons ──────────────────────────────────
        btn_row = BoxLayout(size_hint_y=None, height=38, spacing=8)
        run_btn = Button(text='EJECUTAR', font_name=FONT_MONO, font_size='11sp',
                         bold=True, background_color=(0,0,0,0), color=BLACK)
        with run_btn.canvas.before:
            Color(*ACCENT)
            run_btn._rect = Rectangle(pos=run_btn.pos, size=run_btn.size)
        run_btn.bind(pos=lambda i,v: setattr(i._rect,'pos',v),
                     size=lambda i,v: setattr(i._rect,'size',v))
        run_btn.bind(on_press=lambda *a: self._run())

        clr_btn = Button(text='LIMPIAR', font_name=FONT_MONO, font_size='11sp',
                         background_color=(0,0,0,0), color=TEXT2,
                         size_hint_x=None, width=90)
        with clr_btn.canvas.before:
            Color(*BG3)
            clr_btn._rect = Rectangle(pos=clr_btn.pos, size=clr_btn.size)
            Color(*BORDER2)
            clr_btn._line = Line(rectangle=(*clr_btn.pos, *clr_btn.size), width=1)
        clr_btn.bind(pos=lambda i,v: (setattr(i._rect,'pos',v), setattr(i._line,'rectangle',(*v,*i.size))),
                     size=lambda i,v: (setattr(i._rect,'size',v), setattr(i._line,'rectangle',(*i.pos,*v))))
        clr_btn.bind(on_press=lambda *a: self._clear())

        btn_row.add_widget(run_btn)
        btn_row.add_widget(clr_btn)
        inner.add_widget(btn_row)

        # ── Quick pills ──────────────────────────────
        pills_grid = GridLayout(cols=4, size_hint_y=None, spacing=5)
        pills_grid.bind(minimum_height=pills_grid.setter('height'))
        for label, prompt in QUICK:
            p = Button(text=label, font_name=FONT_MONO, font_size='9sp',
                       color=TEXT2, background_color=(0,0,0,0),
                       size_hint_y=None, height=28)
            with p.canvas.before:
                Color(*BG3)
                p._r = Rectangle(pos=p.pos, size=p.size)
                Color(*BORDER2)
                p._l = Line(rectangle=(*p.pos, *p.size), width=1)
            p.bind(pos=lambda i,v: (setattr(i._r,'pos',v), setattr(i._l,'rectangle',(*v,*i.size))),
                   size=lambda i,v: (setattr(i._r,'size',v), setattr(i._l,'rectangle',(*i.pos,*v))))
            _prompt = prompt
            p.bind(on_press=lambda i, pr=_prompt: self._set_prompt(pr))
            pills_grid.add_widget(p)
        inner.add_widget(pills_grid)

        # ── Output area ──────────────────────────────
        self.output_card = CardBox(orientation='vertical', size_hint_y=None,
                                   padding=10, spacing=4)
        self.output_card.opacity = 0
        out_sec = SectionLabel('output')
        self.result_lbl = _make_label('', font_size='12sp', color=TEXT)
        self.output_card.add_widget(out_sec)
        self.output_card.add_widget(self.result_lbl)
        self.output_card.bind(
            minimum_height=self.output_card.setter('height')
        )
        # make it a proper layout
        self.output_card.size_hint_y = None
        self.output_card.bind(minimum_height=self.output_card.setter('height'))

        inner.add_widget(self.output_card)

        # ── History ──────────────────────────────────
        inner.add_widget(SectionLabel('historial'))
        self.history_box = BoxLayout(orientation='vertical', spacing=6,
                                     size_hint_y=None)
        self.history_box.bind(minimum_height=self.history_box.setter('height'))
        inner.add_widget(self.history_box)

        sv.add_widget(inner)
        root.add_widget(sv)
        self.add_widget(root)

        self._load_history()

    # ── Actions ─────────────────────────────────────
    def _set_prompt(self, txt):
        self.text_input.text = txt

    def _clear(self):
        self.text_input.text = ''
        self.output_card.opacity = 0
        self.result_lbl.text = ''

    def _run(self):
        q = self.text_input.text.strip()
        if not q:
            return
        self.output_card.opacity = 1
        self.result_lbl.text = '[color=#444444]● calculando...[/color]'
        self.result_lbl.markup = True
        threading.Thread(target=self._compute, args=(q,), daemon=True).start()

    def _compute(self, q):
        try:
            text = math_resolver(q)
        except Exception as e:
            text = f'Error: {e}'
        Clock.schedule_once(lambda dt: self._show_result(q, text))

    def _show_result(self, q, text):
        self.result_lbl.markup = False
        self.result_lbl.text = text
        storage.add_history(q, text)
        self._load_history()

    def _load_history(self):
        self.history_box.clear_widgets()
        for item in storage.get_history():
            self.history_box.add_widget(
                HistoryItem(item['q'], item['a'], padding=8)
            )
