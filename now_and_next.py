import tkinter as TK

class App(TK.Frame):
    def __init__(self,master):    
        TK.Frame.__init__(self,master,padx=20, pady=15)
        self.pack(expand=TK.YES, fill=TK.BOTH)

        self.master.title('Hello World')
        self.master.tk_setPalette(background='#e6e6e6')

        TK.Frame(self, width=200, height=300, 
            bg='red').pack(side=TK.LEFT, fill=TK.BOTH)
        TK.Frame(self, width=300, height=300, 
            bg='green').pack(side=TK.RIGHT, fill=TK.BOTH, expand=TK.YES)

if __name__ == "__main__":
    root = TK.Tk()
    app = App(root)
    app.mainloop()