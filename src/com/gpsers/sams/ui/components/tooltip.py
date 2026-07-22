import tkinter as tk

class ToolTip(object):
    def __init__(self, widget, text='widget info'):
        self.widget = widget
        self.text = text
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)
        self.widget.bind("<ButtonPress>", self.leave)
        self.id = None
        self.tw = None

    def enter(self, event=None):
        self.schedule()

    def leave(self, event=None):
        self.unschedule()
        self.hidetip()

    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(500, self.showtip)

    def unschedule(self):
        id = self.id
        self.id = None
        if id:
            self.widget.after_cancel(id)

    def showtip(self, event=None):
        try:
            x = self.widget.winfo_rootx() + 20
            y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
            self.tw = tk.Toplevel(self.widget)
            self.tw.wm_overrideredirect(True)
            self.tw.wm_geometry("+%d+%d" % (x, y))
            
            # Estilo escuro moderno para combinar com o SAMS
            label = tk.Label(self.tw, text=self.text, justify='left',
                           background="#2b2b2b", relief='solid', borderwidth=1,
                           font=("Segoe UI", 10, "normal"), fg="#E6EDF3")
            label.pack(ipadx=6, ipady=4)
        except Exception:
            pass

    def hidetip(self):
        if self.tw:
            self.tw.destroy()
            self.tw = None
