"""
CALC//SYS — Math Solver + Daily Sudoku
APK con Python + Kivy
"""
import os
os.environ.setdefault('KIVY_NO_ENV_CONFIG', '1')

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, NoTransition
from kivy.core.window import Window
from kivy.utils import get_color_from_hex

from screens.solver import SolverScreen
from screens.sudoku import SudokuScreen
from screens.nav import NavBar
from kivy.uix.boxlayout import BoxLayout

# Dark terminal palette
BG       = get_color_from_hex('#080808')
Window.clearcolor = BG


class RootLayout(BoxLayout):
    def __init__(self, **kw):
        super().__init__(orientation='vertical', **kw)

        self.sm = ScreenManager(transition=NoTransition())
        self.sm.add_widget(SolverScreen(name='solver'))
        self.sm.add_widget(SudokuScreen(name='sudoku'))

        self.nav = NavBar(switch_cb=self.switch_screen)

        self.add_widget(self.sm)
        self.add_widget(self.nav)

    def switch_screen(self, name):
        self.sm.current = name
        self.nav.set_active(name)


class CalcSysApp(App):
    title = 'CALC//SYS'

    def build(self):
        Window.softinput_mode = 'below_target'
        return RootLayout()


if __name__ == '__main__':
    CalcSysApp().run()
