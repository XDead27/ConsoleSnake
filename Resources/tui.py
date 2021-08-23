#!/usr/bin/env python

import curses
from curses import panel

class TextPanel(object):
    def __init__(self, spawn_y, spawn_x, stdscreen):
        self.stdscreen = stdscreen

        self.spawn_y = spawn_y
        self.spawn_x = spawn_x

        self.window = stdscreen.subwin(spawn_y, spawn_x)
        self.panel = panel.new_panel(self.window)
        self.panel.hide()
        panel.update_panels()

    def set_window_size(self, y, x):
        self.window = self.stdscreen.subwin(y, x, self.spawn_y, self.spawn_x)
        self.panel = panel.new_panel(self.window)
        self.panel.hide()
        panel.update_panels()

    def display(self):
        self.panel.top()
        self.panel.show()
        self.window.clear()
        self.window.refresh()
        curses.doupdate()

    def add_text(self, text, y = 1, x = 1, mode = curses.A_NORMAL):
        self.window.addstr(y, x, text, mode)
        self.window.refresh()
        curses.doupdate()

    def hide(self):
        self.window.clear()
        self.panel.hide()
        panel.update_panels()
        curses.doupdate()

class PanelList(TextPanel):
    def __init__(self, spawn_y, spawn_x, items, stdscreen):
        super(PanelList, self).__init__(spawn_y, spawn_x, stdscreen)

        self.items = items
        self.window.border(0, 0, 0, 0, 0, 0, 0, 0)
        self.display()

    def display(self):
        super(PanelList, self).display()
        self.refresh()

    def refresh(self):
        for i in range(len(self.items)):
            self.window.addstr(1 + i, 1, self.items[i], curses.A_NORMAL)
        self.window.refresh()
        curses.doupdate()
    
    def add_entry(self, item):
        self.items.append(item)
        self.refresh()

class Menu(TextPanel):
    def __init__(self, items, spawn_y, spawn_x, stdscreen, vertical = True):
        super(Menu, self).__init__(spawn_y, spawn_x, stdscreen)

        self.window.keypad(1)
        self.vertical = vertical

        self.position = 0
        self.items = items
        self.items.append(("exit", "exit"))

    def set_items(self, new_items):
        self.window.clear()
        self.items = new_items
        self.items.append(("exit", "exit"))

    def navigate(self, n):
        self.position += n
        if self.position < 0:
            self.position = 0
        elif self.position >= len(self.items):
            self.position = len(self.items) - 1

    def display(self):
        self.panel.top()
        self.panel.show()
        self.window.clear()

        while True:
            self.window.refresh()
            curses.doupdate()
            for index, item in enumerate(self.items):
                if index == self.position:
                    mode = curses.A_REVERSE
                else:
                    mode = curses.A_NORMAL

                msg = "-o- %s" % (item[0])
                if self.vertical:
                    self.window.addstr(1 + index, 1, msg, mode)
                else:
                    self.window.addstr(1, 1 + (index*20), msg, mode)

            key = self.window.getch()

            if key in [curses.KEY_ENTER, ord("\n")]:
                if self.position == len(self.items) - 1:
                    break
                else:
                    self.items[self.position][1]()


            elif key == curses.KEY_UP:
                self.navigate(-1)

            elif key == curses.KEY_DOWN:
                self.navigate(1)

        self.hide()

class InputBox(TextPanel):
    def __init__(self, y, x, stdscreen, prompt):
        super(InputBox, self).__init__(y, x, stdscreen)

        curses.curs_set(1)
        self.window.keypad(1)
        self.window.refresh()

        self.prompt = prompt

    def hide(self):
        self.window.bkgd(' ', curses.A_NORMAL)

        super(InputBox, self).hide()

    def display(self):
        curses.echo()

        super(InputBox, self).display()

        if curses.has_colors():
            curses.init_pair(70, curses.COLOR_GREEN, curses.COLOR_GREEN)
            curses.init_pair(71, curses.COLOR_CYAN, curses.COLOR_BLACK)
            self.window.addstr(2, 3, self.prompt, curses.A_NORMAL)
            self.window.addstr(4, 3, " "*15, curses.color_pair(70))
        else:
            self.window.addstr(2, 3, self.prompt, curses.A_NORMAL)
        
        self.window.bkgd(' ', curses.A_REVERSE | curses.A_BOLD)

        got_string = self.window.getstr(4, 3)

        self.hide()
        curses.curs_set(0)
        curses.noecho()

        return bytes.decode(got_string)

class OptionsBox(TextPanel):
    def __init__(self, y, x, stdscreen, prompt, items, vertical=True):
        super(OptionsBox, self).__init__(y, x, stdscreen)

        self.window.keypad(1)
        self.vertical = vertical
        self.prompt = prompt

        self.position = 0
        self.items = items
        self.items.append("abort")
        
    def navigate(self, n):
        self.position += n
        if self.position < 0:
            self.position = 0
        elif self.position >= len(self.items):
            self.position = len(self.items) - 1

    def display(self):
        self.panel.top()
        self.panel.show()
        self.window.clear()

        while True:
            self.window.refresh()
            curses.doupdate()

            self.window.addstr(1, 1, self.prompt, curses.A_NORMAL)

            for index, item in enumerate(self.items):
                if index == self.position:
                    mode = curses.A_REVERSE
                else:
                    mode = curses.A_NORMAL

                msg = "> %s" % (item)
                
                if self.vertical:
                    self.window.addstr(4 + index, 1, msg, mode)
                else:
                    self.window.addstr(4, 1 + (index*20), msg, mode)  
                          
            key = self.window.getch()

            if key in [curses.KEY_ENTER, ord("\n")]:
                self.hide()
                return self.items[self.position]


            elif key == curses.KEY_UP:
                self.navigate(-1)

            elif key == curses.KEY_DOWN:
                self.navigate(1)