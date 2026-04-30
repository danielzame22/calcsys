# screens/sudoku.py
import random
from datetime import date

from kivy.uix.screen import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle, Line, RoundedRectangle

import storage
from sudoku_engine import generate_daily_puzzle, solve_board
from theme import *


def _bg(widget, color):
    with widget.canvas.before:
        Color(*color)
        rect = Rectangle(pos=widget.pos, size=widget.size)
    widget.bind(pos=lambda *a: setattr(rect, 'pos', widget.pos),
                size=lambda *a: setattr(rect, 'size', widget.size))


def _sec_label(txt):
    l = Label(text=f'// {txt.upper()}', font_size='9sp', color=TEXT3,
              halign='left', font_name=FONT_MONO, size_hint_y=None, height=22)
    l.bind(width=lambda i, v: setattr(i, 'text_size', (v, None)))
    return l


class CellBtn(Button):
    def __init__(self, idx, **kw):
        super().__init__(
            text='', font_size='16sp', font_name=FONT_MONO,
            background_color=(0, 0, 0, 0), color=TEXT,
            bold=False,
            **kw
        )
        self.idx = idx
        self._state = 'empty'  # empty | given | selected | error | correct
        self._draw()

    def _draw(self):
        self.canvas.before.clear()
        row, col = divmod(self.idx, 9)
        with self.canvas.before:
            # background
            if self._state == 'selected':
                Color(*ACCENT_DIM)
            elif self._state == 'given':
                Color(0, 1, 0.53, 0.06)
            elif self._state == 'error':
                Color(1, 0.27, 0.27, 0.12)
            else:
                Color(*BG2)
            Rectangle(pos=self.pos, size=self.size)

            # borders — thin
            Color(*BORDER)
            Line(rectangle=(*self.pos, *self.size), width=1)

            # thick box borders
            if col % 3 == 0 and col != 0:
                Color(*BORDER2)
                Line(points=[self.x, self.y, self.x, self.top], width=2)
            if row % 3 == 0 and row != 0:
                Color(*BORDER2)
                Line(points=[self.x, self.top, self.right, self.top], width=2)

        # text color
        if self._state == 'given':
            self.color = ACCENT
            self.bold = True
        elif self._state == 'error':
            self.color = RED
            self.bold = False
        elif self._state == 'correct':
            self.color = ACCENT
            self.bold = False
        elif self._state == 'selected':
            self.color = WHITE
            self.bold = False
        else:
            self.color = TEXT
            self.bold = False

    def set_state(self, state, value=None):
        self._state = state
        if value is not None:
            self.text = str(value) if value != 0 else ''
        self._draw()

    def on_size(self, *a): self._draw()
    def on_pos(self, *a): self._draw()


class StreakBanner(BoxLayout):
    def __init__(self, **kw):
        super().__init__(
            orientation='horizontal', size_hint_y=None, height=80,
            padding=12, spacing=12, **kw
        )
        with self.canvas.before:
            Color(*BG2)
            self._bg = Rectangle(pos=self.pos, size=self.size)
            Color(*BORDER2)
            self._line = Line(rectangle=(*self.pos, *self.size), width=1)
        self.bind(pos=self._upd, size=self._upd)

        self.num_lbl = Label(
            text='0', font_size='36sp', color=YELLOW,
            font_name=FONT_MONO, bold=True,
            size_hint_x=None, width=70,
            halign='center', valign='middle'
        )

        info = BoxLayout(orientation='vertical', spacing=2)
        title = Label(text='RACHA DIARIA', font_size='9sp', color=TEXT3,
                      font_name=FONT_MONO, halign='left', size_hint_y=None, height=18)
        title.bind(width=lambda i,v: setattr(i,'text_size',(v,None)))
        self.msg_lbl = Label(text='Completa el sudoku de hoy', font_size='11sp',
                             color=TEXT2, font_name=FONT_MONO, halign='left',
                             size_hint_y=None, height=18)
        self.msg_lbl.bind(width=lambda i,v: setattr(i,'text_size',(v,None)))
        self.dots_row = BoxLayout(size_hint_y=None, height=12, spacing=4)
        self._dot_widgets = []
        for _ in range(7):
            d = Label(text='●', font_size='8sp', color=BORDER2)
            self.dots_row.add_widget(d)
            self._dot_widgets.append(d)

        info.add_widget(title)
        info.add_widget(self.msg_lbl)
        info.add_widget(self.dots_row)

        self.add_widget(self.num_lbl)
        self.add_widget(info)

    def _upd(self, *a):
        self._bg.pos = self.pos; self._bg.size = self.size
        self._line.rectangle = (*self.pos, *self.size)

    def update(self, streak, completed_today):
        self.num_lbl.text = str(streak)
        self.msg_lbl.text = ('✓ Completado hoy — Vuelve mañana'
                             if completed_today else
                             'Completa el sudoku de hoy')
        for i, d in enumerate(self._dot_widgets):
            d.color = YELLOW if i < min(streak, 7) else BORDER2


class SudokuScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.puzzle = []
        self.solution = []
        self.board = []
        self.given = []
        self.selected = -1
        self.completed = False
        self.cells = []
        self._build()
        self._load_puzzle()

    def _build(self):
        root = BoxLayout(orientation='vertical', padding=10, spacing=8)
        _bg(root, BG)

        sv = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        inner = BoxLayout(orientation='vertical', spacing=10,
                          size_hint_y=None, padding=[0, 0, 0, 16])
        inner.bind(minimum_height=inner.setter('height'))

        # ── Date / diff ──────────────────────────────
        meta = BoxLayout(size_hint_y=None, height=22)
        self.date_lbl = Label(
            text=date.today().strftime('%A %d %B %Y').upper(),
            font_size='9sp', color=TEXT3, font_name=FONT_MONO,
            halign='left'
        )
        self.date_lbl.bind(width=lambda i,v: setattr(i,'text_size',(v,None)))
        self.diff_lbl = Label(
            text='MEDIO', font_size='9sp', color=TEXT2, font_name=FONT_MONO,
            halign='right'
        )
        self.diff_lbl.bind(width=lambda i,v: setattr(i,'text_size',(v,None)))
        meta.add_widget(self.date_lbl)
        meta.add_widget(self.diff_lbl)
        inner.add_widget(meta)

        # ── Completed banner ─────────────────────────
        self.done_lbl = Label(
            text='✓ SUDOKU COMPLETADO — Vuelve mañana',
            font_size='11sp', color=ACCENT, font_name=FONT_MONO,
            halign='center', size_hint_y=None, height=0, opacity=0
        )
        inner.add_widget(self.done_lbl)

        # ── Grid ─────────────────────────────────────
        grid_wrap = BoxLayout(size_hint_y=None, height=340)
        self.grid = GridLayout(cols=9, spacing=0)
        _bg(self.grid, BG)
        with self.grid.canvas.before:
            Color(*ACCENT2)
            self._grid_border = Line(rectangle=(*self.grid.pos, *self.grid.size), width=2)
        self.grid.bind(pos=self._upd_grid_border, size=self._upd_grid_border)

        for i in range(81):
            c = CellBtn(idx=i)
            c.bind(on_press=lambda btn: self._select(btn.idx))
            self.cells.append(c)
            self.grid.add_widget(c)

        grid_wrap.add_widget(self.grid)
        inner.add_widget(grid_wrap)

        # ── Numpad ───────────────────────────────────
        pad = GridLayout(cols=5, size_hint_y=None, height=100, spacing=6)
        for n in range(1, 10):
            b = Button(text=str(n), font_name=FONT_MONO, font_size='18sp',
                       color=TEXT, background_color=(0,0,0,0))
            with b.canvas.before:
                Color(*BG3)
                b._r = Rectangle(pos=b.pos, size=b.size)
                Color(*BORDER2)
                b._l = Line(rectangle=(*b.pos, *b.size), width=1)
            b.bind(pos=lambda i,v: (setattr(i._r,'pos',v), setattr(i._l,'rectangle',(*v,*i.size))),
                   size=lambda i,v: (setattr(i._r,'size',v), setattr(i._l,'rectangle',(*i.pos,*v))))
            _n = n
            b.bind(on_press=lambda inst, num=_n: self._enter(num))
            pad.add_widget(b)
        # erase
        er = Button(text='⌫', font_name=FONT_MONO, font_size='14sp',
                    color=RED, background_color=(0,0,0,0))
        with er.canvas.before:
            Color(*BG3)
            er._r = Rectangle(pos=er.pos, size=er.size)
            Color(*BORDER2)
            er._l = Line(rectangle=(*er.pos, *er.size), width=1)
        er.bind(pos=lambda i,v: (setattr(i._r,'pos',v), setattr(i._l,'rectangle',(*v,*i.size))),
                size=lambda i,v: (setattr(i._r,'size',v), setattr(i._l,'rectangle',(*i.pos,*v))))
        er.bind(on_press=lambda *a: self._enter(0))
        pad.add_widget(er)
        inner.add_widget(pad)

        # ── Action buttons ───────────────────────────
        acts = BoxLayout(size_hint_y=None, height=40, spacing=8)
        for label, cb in [('VERIFICAR', self._check),
                          ('PISTA', self._hint),
                          ('RESOLVER', self._solve_all)]:
            b = Button(text=label, font_name=FONT_MONO, font_size='10sp',
                       color=TEXT2 if label != 'RESOLVER' else BLACK,
                       background_color=(0,0,0,0),
                       bold=(label == 'RESOLVER'))
            if label == 'RESOLVER':
                with b.canvas.before:
                    Color(*ACCENT)
                    b._r = Rectangle(pos=b.pos, size=b.size)
                b.bind(pos=lambda i,v: setattr(i._r,'pos',v),
                       size=lambda i,v: setattr(i._r,'size',v))
            else:
                with b.canvas.before:
                    Color(*BG3)
                    b._r = Rectangle(pos=b.pos, size=b.size)
                    Color(*BORDER2)
                    b._l = Line(rectangle=(*b.pos, *b.size), width=1)
                b.bind(pos=lambda i,v: (setattr(i._r,'pos',v), setattr(i._l,'rectangle',(*v,*i.size))),
                       size=lambda i,v: (setattr(i._r,'size',v), setattr(i._l,'rectangle',(*i.pos,*v))))
            b.bind(on_press=lambda inst, fn=cb: fn())
            acts.add_widget(b)
        inner.add_widget(acts)

        # ── Streak banner ────────────────────────────
        self.streak_banner = StreakBanner()
        inner.add_widget(self.streak_banner)

        sv.add_widget(inner)
        root.add_widget(sv)
        self.add_widget(root)

    def _upd_grid_border(self, *a):
        self._grid_border.rectangle = (*self.grid.pos, *self.grid.size)

    # ── Puzzle loading ───────────────────────────────
    def _load_puzzle(self):
        self.puzzle, self.solution = generate_daily_puzzle()
        self.given = [v != 0 for v in self.puzzle]

        prog = storage.get_sudoku_progress()
        if prog and prog.get('board'):
            self.board = prog['board']
            self.completed = prog.get('completed', False)
        else:
            self.board = list(self.puzzle)
            self.completed = False

        givens = sum(self.given)
        diff = 'FÁCIL' if givens >= 36 else 'MEDIO' if givens >= 28 else 'DIFÍCIL'
        self.diff_lbl.text = diff

        if self.completed:
            self.done_lbl.height = 28
            self.done_lbl.opacity = 1

        self._render_all()
        self._update_streak_ui()

    def _render_all(self):
        for i, cell in enumerate(self.cells):
            if self.given[i]:
                cell.set_state('given', self.board[i])
            else:
                val = self.board[i]
                cell.set_state('empty' if val == 0 else 'correct', val)

    def _update_streak_ui(self):
        streak, last = storage.get_streak()
        completed_today = (last == storage.today())
        self.streak_banner.update(streak, completed_today)

    # ── Interactions ─────────────────────────────────
    def _select(self, idx):
        if self.given[idx] or self.completed:
            return
        self.selected = idx
        for i, c in enumerate(self.cells):
            if not self.given[i] and c._state not in ('error', 'correct'):
                c.set_state('empty', self.board[i])
        self.cells[idx].set_state('selected', self.board[idx])

    def _enter(self, num):
        if self.selected == -1 or self.given[self.selected] or self.completed:
            return
        self.board[self.selected] = num
        self.cells[self.selected].set_state('empty' if num == 0 else 'empty', num)
        storage.save_sudoku_progress(self.board, self.completed)

    def _check(self):
        all_ok = True
        for i, cell in enumerate(self.cells):
            if not self.given[i]:
                if self.board[i] == 0:
                    all_ok = False
                    cell.set_state('empty', 0)
                elif self.board[i] == self.solution[i]:
                    cell.set_state('correct', self.board[i])
                else:
                    cell.set_state('error', self.board[i])
                    all_ok = False
        if all_ok and all(v != 0 for v in self.board):
            self._complete(by_user=True)

    def _hint(self):
        if self.completed:
            return
        wrong = [i for i in range(81)
                 if not self.given[i] and self.board[i] != self.solution[i]]
        if not wrong:
            return
        idx = random.choice(wrong)
        self.board[idx] = self.solution[idx]
        self.cells[idx].set_state('correct', self.solution[idx])
        self.selected = -1
        storage.save_sudoku_progress(self.board, self.completed)

    def _solve_all(self):
        self.board = list(self.solution)
        self.completed = True
        for i, cell in enumerate(self.cells):
            if self.given[i]:
                cell.set_state('given', self.board[i])
            else:
                cell.set_state('correct', self.board[i])
        storage.save_sudoku_progress(self.board, True)
        self.done_lbl.height = 28
        self.done_lbl.opacity = 1
        # No streak for auto-solve

    def _complete(self, by_user=True):
        self.completed = True
        storage.save_sudoku_progress(self.board, True)
        self.done_lbl.height = 28
        self.done_lbl.opacity = 1

        if by_user:
            streak = storage.record_completion()
            self._update_streak_ui()
            self._show_success_popup(streak)

    def _show_success_popup(self, streak):
        content = BoxLayout(orientation='vertical', padding=20, spacing=12)
        _bg(content, BG2)

        content.add_widget(Label(
            text='COMPLETADO', font_size='20sp', color=ACCENT,
            font_name=FONT_MONO, bold=True, size_hint_y=None, height=40
        ))
        content.add_widget(Label(
            text=f'🔥  {streak}', font_size='44sp', color=YELLOW,
            font_name=FONT_MONO, size_hint_y=None, height=60
        ))
        content.add_widget(Label(
            text='DÍAS DE RACHA', font_size='11sp', color=TEXT2,
            font_name=FONT_MONO, size_hint_y=None, height=24
        ))

        close_btn = Button(
            text='CONTINUAR', font_name=FONT_MONO, font_size='12sp',
            bold=True, color=BLACK, background_color=(0,0,0,0),
            size_hint_y=None, height=44
        )
        with close_btn.canvas.before:
            Color(*ACCENT)
            close_btn._r = Rectangle(pos=close_btn.pos, size=close_btn.size)
        close_btn.bind(pos=lambda i,v: setattr(i._r,'pos',v),
                       size=lambda i,v: setattr(i._r,'size',v))

        popup = Popup(
            title='', content=content,
            size_hint=(.8, .5),
            separator_height=0,
            background='',
            background_color=(0, 0, 0, .95),
        )
        close_btn.bind(on_press=popup.dismiss)
        content.add_widget(close_btn)
        popup.open()
