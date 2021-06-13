import tkinter as TK

class App(TK.Frame):
    def __init__(self,master):    
        TK.Frame.__init__(self,master,padx=20, pady=15)
        self.pack(expand=TK.YES, fill=TK.BOTH)

        self.master.title('Hello World')
        self.master.tk_setPalette(background='#e6e6e6')

        TK.Frame(self, width=140, height=140, 
            bg='red').pack(side=TK.LEFT, fill=TK.BOTH)
        TK.Frame(self, width=280, height=140, 
            bg='green').pack(side=TK.RIGHT, fill=TK.BOTH, expand=TK.YES)

if __name__ == "__main__":
    root = TK.Tk()
    app = App(root)
    root.wm_attributes("-topmost", 1)
    app.mainloop()