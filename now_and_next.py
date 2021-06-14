import tkinter as TK

CLOCK_FACE_COLOR='white'
ARC_COLOR='pink'
CLOCK_PADDING=50

def biggest_square(x1,y1,x2,y2):
    """ return x,y,x2,y2 for a square centered in the given 
    rectangle, expressed as x1,y1,x2,y2 i.e. NOT width and height.
    """
    width=x2-x1
    height=y2-y1
    square_side = min(width,height)
    ofs_x = width-square_side
    ofs_y = height-square_side
    return (x1+ofs_x,y1+ofs_y,x2-ofs_x,y2-ofs_y)

class TimerWidget(TK.Canvas):
    def __init__(self, parent, **kwargs):
        TK.Canvas.__init__(self, parent, highlightthickness=0, **kwargs)
        self.bind("<Configure>", self.on_resize)
        self.height = self.winfo_reqheight()
        self.width = self.winfo_reqwidth()

        x1,y1,x2,y2 = biggest_square(0,0,self.width,self.height)

        self.create_oval(CLOCK_PADDING, 
                         CLOCK_PADDING,
                         self.height-CLOCK_PADDING,
                         self.height-CLOCK_PADDING,
                         fill=CLOCK_FACE_COLOR)
        self.clock_arc=self.create_arc(CLOCK_PADDING+5,
                        CLOCK_PADDING+5,
                        self.height-CLOCK_PADDING-5,
                        self.height-CLOCK_PADDING-5,
                        start=90,
                        extent=-180,
                        fill=ARC_COLOR,
                        outline="")
        self.clock_label = self.create_text(self.height/2,self.height/2,justify=TK.CENTER,text="00:00",font=('Monoid','22',''))
        self.addtag_all('all')

    def on_resize(self,event):
        # determine the ratio of old width/height to new width/height
        scale = float(event.height)/self.height
        self.width = event.width
        self.height = event.height
        # resize the canvas 
        self.config(width=self.width, height=self.height)
        # rescale all the objects tagged with the "all" tag
        self.scale("all",0,0,scale,scale)

    def set_time( self, delta ):
        """ given a timedelta, update the clockface.
        right now the face is 1 hour in minutes.
        """
        seconds = delta.total_seconds()
        # The sweep goes in half-minute increments
        degrees = float(seconds // 30) * -3.0
        self.itemconfig(self.clock_arc, extent=degrees)
        minutes = int(seconds / 60)
        seconds=int(seconds) % 60
        self.itemconfig(self.clock_label, text=f'{int(minutes):02}:{seconds:02}')

class App(TK.Frame):
    def __init__(self,master):    
        TK.Frame.__init__(self,master,padx=20, pady=15)
        self.pack(expand=TK.YES, fill=TK.BOTH)

        self.master.title('Hello World')
        self.master.tk_setPalette(background='#e6e6e6')

        left_frame = TK.Frame(self, width=140, height=140, 
            bg='red')
        self.clock_face=TimerWidget(left_frame, width=140,height=140 ).pack(side=TK.TOP)
        left_frame.pack(side=TK.LEFT, fill=TK.BOTH)

        right_frame=TK.Frame(self, width=280, height=140, 
            bg='green')
        self.next_label = TK.Label(right_frame, text='Awaiting data...',justify=TK.LEFT)
        self.next_label.pack(side=TK.LEFT, expand=TK.YES, fill=TK.BOTH)
        right_frame.pack(side=TK.RIGHT, expand=TK.YES, fill=TK.BOTH)


if __name__ == "__main__":
    root = TK.Tk()
    app = App(root)
    root.wm_attributes("-topmost", 1)
    app.mainloop()