import tkinter as TK

class App(TK.Frame):
    def __init__(self,master):    
        TK.Frame.__init__(self,master,padx=20, pady=15)
        self.pack(expand=TK.YES, fill=TK.BOTH)

        self.master.title('Hello World')
        self.master.tk_setPalette(background='#e6e6e6')

        left_frame = TK.Frame(self, width=140, height=140, 
            bg='red')
        TK.Frame(self, width=280, height=140, 
            bg='green').pack(side=TK.RIGHT, fill=TK.BOTH, expand=TK.YES)

        TK.Canvas(left_frame, width=100,height=100, bg='yellow').pack()
        left_frame.pack(side=TK.LEFT, fill=TK.BOTH)

if __name__ == "__main__":
    root = TK.Tk()
    app = App(root)
    root.wm_attributes("-topmost", 1)
    app.mainloop()