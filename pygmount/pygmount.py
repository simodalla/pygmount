#!/usr/bin/env python
# -*- coding: utf-8 -*-

from Tkinter import *
from ttk import *


class Application(Frame):

    def say_hi(self):
        print "hi there, everyone!"

    def create_widgets(self):
        self.QUIT = Button(self)
        self.QUIT["text"] = "QUIT"
        self.QUIT["fg"]   = "red"
        self.QUIT["command"] =  self.quit

        self.QUIT.pack({"side": "left"})

        self.hi_there = Button(self)
        self.hi_there["text"] = "Hello",
        self.hi_there["command"] = self.say_hi

        self.hi_there.pack({"side": "left"})

    def __init__(self, master=None):
        Frame.__init__(self, master)
        self.pack()
        self.create_widgets()

root = Tk()
style = ttk.Style()
style.configure("BW.TLabel", foreground="black", background="white")
app = Application(master=root)
app.mainloop()
root.destroy()
