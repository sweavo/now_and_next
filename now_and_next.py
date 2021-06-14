"""
TODO

Set a minimum size or stop the clockface from breaking when you go too small
"""
import datetime

import tkinter as TK

CLOCK_FACE_COLOR='white'
ARC_COLOR='pink'
CLOCK_PADDING=10

## Time Stuff

DEBUG_TIME_OFFSET=datetime.timedelta(seconds=3600)
#DEBUG_TIME_OFFSET=datetime.timedelta(hours=-10,seconds=900)
def get_cursor():
    """ Return the time that we are interested in """
    cursor=datetime.datetime.now(datetime.timezone.utc) + DEBUG_TIME_OFFSET
    # log what time offset caused 
    return cursor

## Calendar/Outlook stuff

## UI stuffs

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

class NowAndNextUI(TK.Frame):
    def __init__(self,master):    
        TK.Frame.__init__(self,master,padx=20, pady=15)
        self.pack(expand=TK.YES, fill=TK.BOTH)

        left_frame = TK.Frame(self, width=140, height=140)
        self.clock_face=TimerWidget(left_frame, width=140,height=140).pack(side=TK.TOP)
        left_frame.pack(side=TK.LEFT, fill=TK.BOTH)

        right_frame=TK.Frame(self, width=280, height=140)
        self.next_label = TK.Label(right_frame, text='Awaiting data...',justify=TK.LEFT)
        self.next_label.pack(side=TK.LEFT, expand=TK.YES, fill=TK.BOTH)
        right_frame.pack(side=TK.RIGHT, expand=TK.YES, fill=TK.BOTH)

    def refresh_canvas(self):
        self.after(1000, self.refresh_canvas)
        time_now = get_cursor()

        if time_now.minute != self.previous_minute:
            ongoing, upcoming = refresh_database(time_now)
            self.next_deadline = upcoming.start
            self.previous_minute = time_now.minute
            lines = [time_now.strftime('%c')]
            lines.extend(map( lambda ev: f'    {ev[0].subject}', ongoing )) 
            lines.append(f'Next:\n    {upcoming.subject}')
            
            self.next_label.config(text='\n'.join(lines))

        self.clock_face.set_time( self.next_deadline - time_now )


    def mainloop(self):
        self.previous_minute = None
        self.after(1000, self.refresh_canvas)
        self.master.mainloop()


if __name__ == "__main__":
    root = TK.Tk()
    app = NowAndNextUI(root)
    root.title('Now & Next')
    root.attributes('-topmost', 1)
    root.geometry(f'450x150')

    root.wm_attributes("-topmost", 1)
    app.mainloop()
