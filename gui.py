import tkinter as tk
from ca_logging import log
import time
import threading


class GUI(tk.Tk):
    def __init__(self, server, server_thread):
        tk.Tk.__init__(self)
        self.server = server
        self.server_thread = server_thread
        self.popup = None

    def cannotclose_popup_destroy(self):
        self.popup.destroy()
        self.popup = None

    def cannotclose_popup(self):
        msg = "This window will not close while the server is running.\n\nDo you want to stop the server and quit?"
        self.popup = tk.Tk()
        self.popup.wm_title("!")
        label = tk.Label(self.popup, text=msg)
        label.pack(side="top", fill="x", pady=10)
        B1 = tk.Button(self.popup, text="Yes", command=self.quit)
        B1.pack()
        B2 = tk.Button(self.popup, text="No", command=self.cannotclose_popup_destroy)
        B2.pack()
        self.popup.mainloop()

    def quit(self):
        if self.popup:
            self.popup.destroy()
        thread_name = self.server_thread.name
        self.server.quit(gui_quit=True)
        self.server_thread.join()
        log.info("Thread %s joined, server shut down." % thread_name)
        log.info("Closing GUI.")
        self.destroy()
        exit(0)

    def start_gui(self):
        self.title("CORA server")
        self.geometry('350x200')
        self.protocol("WM_DELETE_WINDOW", self.cannotclose_popup)
        lbl = tk.Label(self, text="Cora server is running")
        lbl.grid(column=0, row=0)
        btn = tk.Button(self, text="Stop server and quit", command=self.quit)
        btn.grid(column=0, row=1)
        log.info("GUI starting")
        self.mainloop()
