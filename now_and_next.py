"""
TODO

Set a minimum size or stop the clockface from breaking when you go too small
"""
from collections import namedtuple
import datetime
import locale
import tkinter as TK
import win32com.client

## Constants for time topic

DEBUG_TIME_OFFSET=datetime.timedelta(seconds=3600) # Manually set for BST, TODO get from the environment
#DEBUG_TIME_OFFSET=datetime.timedelta(hours=0)

## Constants for UI topic

CLOCK_FACE_COLOR='white'
ARC_COLOR='pink'
CLOCK_PADDING=10

## Constants for Calendar/Outlook topic

LANGUAGE='en_GB'

Event = namedtuple("Event", "start subject duration")

olResponseAccepted=3
olResponseDeclined=4
olResponseNone=0
olResponseNotResponded=5
olResponseOrganized=1
olResponseTentative=2

## Code for time topic

def get_cursor():
    """ Return the time that we are interested in """
    cursor=datetime.datetime.now(datetime.timezone.utc) + DEBUG_TIME_OFFSET
    # log what time offset caused 
    return cursor

## Code for Calendar/Outlook topic

def locale_specific_date_string( date_time ):
    """ python on top of Windows needs a little help with locales.
        This function converts a datetime into a string usable by Office queries
    """
    locale.setlocale(locale.LC_ALL, LANGUAGE)
    return date_time.date().strftime('%x')

def getAppointments():
    """ not sure what Outlook this uses, I'm guessing it's the running Outlook
        instance.
    """ 
    outlook_session = win32com.client.Dispatch("Outlook.Application")
    ns = outlook_session.GetNamespace("MAPI")
    return ns.GetDefaultFolder(9).Items

def getCalendarEntries(days=1):
    """
    """
    period_start = datetime.datetime.today()
    after_period_end = datetime.timedelta(days=days) + period_start

    appointments = getAppointments()
    appointments.Sort("[Start]")
    appointments.IncludeRecurrences = "True"

    lsds = locale_specific_date_string # shorter name for readable string below
    restricted_appointments = appointments.Restrict(
        f"[Start] >= '{lsds(period_start)}' AND [Start] < '{lsds(after_period_end)}'")
    
    for appointment in restricted_appointments:
        if appointment.ResponseStatus not in [ olResponseDeclined, olResponseTentative ]:
            yield Event(appointment.Start, appointment.Subject, appointment.Duration)

def get_now_and_next( entries, cursor):
    """ Return a tuple of ( <ongoing events with end times>, <next event including start time> )
    """
    ongoing=[]
    upcoming=[]

    for entry in entries:
        minutes_till_start = (entry.start - cursor) / datetime.timedelta(minutes=1)
        minutes_till_end = minutes_till_start + entry.duration

        record = (entry, cursor + datetime.timedelta(seconds=60*minutes_till_end))

        if minutes_till_start<=0:
            if minutes_till_end>0:
                ongoing.append(record)
        elif minutes_till_start<60:
            upcoming.append(record)
        else:
            return ongoing, upcoming

def refresh_database(cursor):
    """ To be called infrequently, returns a tuple of ongoing, upcoming meetings. """
    events = list( getCalendarEntries(4) )
    return get_now_and_next( events, cursor )

## Code for UI topic

class TimerWidget(TK.Canvas):
    def __init__(self, parent, **kwargs):
        TK.Canvas.__init__(self, parent, highlightthickness=0, **kwargs)
        self.height = self.winfo_reqheight()
        self.width = self.winfo_reqwidth()

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

    def set_time( self, delta ):
        """ given a timedelta, update the clockface.
        right now the face is 1 hour in minutes.
        """
        seconds = min(3600,delta.total_seconds())
        # The sweep goes in half-minute increments
        degrees = float(seconds // 30) * -3.0
        self.itemconfig(self.clock_arc, extent=degrees)
        minutes = int(seconds / 60)
        seconds=int(seconds) % 60
        self.itemconfig(self.clock_label, text=f'{int(minutes):02}:{seconds:02}')

class NowAndNextUI(TK.Frame):
    def __init__(self,master):    
        TK.Frame.__init__(self,master,padx=15, pady=10)
        self.pack(expand=TK.YES, fill=TK.BOTH)

        left_frame = TK.Frame(self, width=140, height=140)
        self.clock_face=TimerWidget(left_frame, width=140,height=140)
        self.clock_face.pack(side=TK.LEFT)
        left_frame.pack(side=TK.LEFT)

        right_frame=TK.Frame(self, width=280, height=140)
        self.next_label = TK.Label(right_frame, text='Awaiting data...',justify=TK.LEFT)
        self.next_label.pack(side=TK.LEFT, expand=TK.YES, fill=TK.BOTH)
        right_frame.pack(side=TK.RIGHT, expand=TK.YES, fill=TK.BOTH)

    def refresh_canvas(self):
        self.after(1000, self.refresh_canvas)
        time_now = get_cursor() # TODO this dependency should be injected

        if time_now.minute != self.previous_minute:
            ongoing, upcoming = refresh_database(time_now)
            self.next_deadline = upcoming[0][0].start
            self.previous_minute = time_now.minute
            lines = [time_now.strftime('%c')]
            lines.extend(map(lambda ev: f'    {ev[0].subject}', ongoing )) 
            lines.append(f'Next:\n    {upcoming[0][0].subject}')
            lines.extend(map(lambda ev: f'    +{int((ev[0].start-self.next_deadline).total_seconds() / 60)}m {ev[0].subject}', upcoming[1:]))
            
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
    root.geometry(f'450x160')

    root.wm_attributes("-topmost", 1)
    app.mainloop()
