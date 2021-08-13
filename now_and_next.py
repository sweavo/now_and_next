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
#DEBUG_TIME_OFFSET=datetime.timedelta(hours=-16)

## Constants for UI topic

CLOCK_FACE_COLOR='white'
ARC_COLORS=['#ffaaaa', '#aaccff', '#ffaaff']
CLOCK_PADDING=10

UI_DATE_FORMAT='%Y-%m-%d %H:%M (CW%V)'

## Constants for Calendar/Outlook topic

olFolderCalendar=9
olFolderConflicts=19
olFolderContacts=10
olFolderDeletedItems=3
olFolderDrafts=16
olFolderInbox=6
olFolderJournal=11
olFolderJunk=23
olFolderLocalFailures=21
olFolderManagedEmail=29
olFolderNotes=12
olFolderOutbox=4
olFolderSentMail=5
olFolderServerFailures=22
olFolderSuggestedContacts=30
olFolderSyncIssues=20
olFolderTasks=13
olFolderToDo=28
olPublicFoldersAllPublicFolders=18
olFolderRssFeeds=25

olResponseAccepted=3
olResponseDeclined=4
olResponseNone=0
olResponseNotResponded=5
olResponseOrganized=1
olResponseTentative=2

## Application data types

Event = namedtuple("Event", "start end subject ")

## Application configuration constants

LANGUAGE='en_GB'


## Code for time topic

def get_cursor():
    """ Return the time that we are interested in """
    cursor=datetime.datetime.now(datetime.timezone.utc) + DEBUG_TIME_OFFSET
    return cursor

## Code for Calendar/Outlook topic

def locale_specific_date_string( date_time ):
    """ python on top of Windows needs a little help with locales.
        This function converts a datetime into a string usable by Office queries
    """
    locale.setlocale(locale.LC_ALL, LANGUAGE)
    return date_time.date().strftime('%x')

def get_standard_folder_items(ol_folder_id):
    """ not sure what Outlook this uses, I'm guessing it's the running Outlook
        instance.
        Get the items from a standard folder
    """
    outlook_session = win32com.client.Dispatch("Outlook.Application")
    ns = outlook_session.GetNamespace("MAPI")
    return ns.GetDefaultFolder(ol_folder_id).Items

def get_calendar_entries_for_preiod(period_start, days=1):
    """ generator function to get the appointments from today for `days` days,
        retrieved from Outlook into a python structure
    """
    after_period_end = datetime.timedelta(days=days) + period_start

    appointments = get_standard_folder_items(olFolderCalendar)
    appointments.Sort("[Start]")
    appointments.IncludeRecurrences = "True"

    lsds = locale_specific_date_string # shorter name for readable string below
    restriction_query = f"[Start] >= '{lsds(period_start)}' AND [Start] < '{lsds(after_period_end)}'"
    restricted_appointments = appointments.Restrict( restriction_query )

    for appointment in restricted_appointments:
        if appointment.ResponseStatus not in [ olResponseDeclined, olResponseTentative ]:
            start_time = appointment.Start
            end_time = start_time + datetime.timedelta(seconds=60 * appointment.Duration)
            yield Event(start_time, end_time, appointment.Subject)

def get_now_and_next( entries, cursor):
    """ Return a tuple of ( <ongoing events with end times>, <next event including start time> )
    """
    ongoing=[]
    upcoming=[]

    for entry in entries:
        minutes_till_start = (entry.start - cursor) / datetime.timedelta(minutes=1)
        minutes_till_end = (entry.end - cursor) / datetime.timedelta(minutes=1)

        if minutes_till_start<=0:
            if minutes_till_end>0:
                ongoing.append(entry)
        elif minutes_till_start<60:
            upcoming.append(entry)
        else:
            break
    return ongoing, upcoming

def refresh_database(cursor):
    """ To be called infrequently, returns a tuple of ongoing, upcoming meetings. """
    events = list( get_calendar_entries_for_preiod(cursor,4) )
    return get_now_and_next( events, cursor )

## Code for UI topic

class TimerWidget(TK.Canvas):
    """ TKInter widget to display a round clockface with a coloured segment to indicate
        minutes remaining
    """
    def __init__(self, parent, **kwargs):
        TK.Canvas.__init__(self, parent, highlightthickness=0, **kwargs)
        self.height = self.winfo_reqheight()
        self.width = self.winfo_reqwidth()

        self.create_oval(CLOCK_PADDING,
                         CLOCK_PADDING,
                         self.height-CLOCK_PADDING,
                         self.height-CLOCK_PADDING,
                         fill=CLOCK_FACE_COLOR)
        self.arcs=[]
        self.clock_label = self.create_text(self.height/2,self.height/2,justify=TK.CENTER,text="00:00",font=('Monoid','22',''))

    def set_time( self, delta ):
        """ given a timedelta, update the clockface.
        right now the face is 1 hour in minutes.
        """
        seconds = min(3600,delta.total_seconds())
        # The sweep goes in half-minute increments
        degrees = float(seconds // 30) * 3.0
        self.set_arcs([degrees])
        minutes=int(seconds / 60)
        seconds=int(seconds) % 60
        self.itemconfig(self.clock_label, text=f'{int(minutes):02}:{seconds:02}')

    def set_times(self, timedeltas ):
        """ given a list of timedeltas, draw the arcs representing them
            timedeltas are relative to one another.
        """
        angles =[]

        for timedelta in timedeltas:
            seconds = min(3600,timedelta.total_seconds())
            angles.append(float(seconds // 30) * 3.0)

        self.set_arcs(angles)

        if len(timedeltas) > 0:
            seconds = min(3600,timedeltas[0].total_seconds())
            minutes=int(seconds / 60)
            seconds=int(seconds) % 60
            self.itemconfig(self.clock_label, text=f'{int(minutes):02}:{seconds:02}')
        self.tag_raise(self.clock_label)

    def set_arcs(self, angle_deltas):
        """ given a list of degrees-of-arc, set the clockface to a series of arcs of those
            subtensions.  Each angle is incremental: [ 45, 45 ] occupies the first 90 degrees
            of the circle.

            Coordinate system is clockwise from north, whereas TkInter's is CCW from east.
        """
        while len(angle_deltas) < len(self.arcs):
            self.delete(self.arcs.pop())

        start=90
        for index, angle_delta in enumerate(angle_deltas):
            extent=-angle_delta
            color=ARC_COLORS[index % len(ARC_COLORS)]

            if index >= len(self.arcs):
                self.arcs.append(
                    self.create_arc(
                        CLOCK_PADDING+5,
                        CLOCK_PADDING+5,
                        self.height-CLOCK_PADDING-5,
                        self.height-CLOCK_PADDING-5,
                        start=start,
                        extent=extent,
                        fill=color,
                        outline=""))
            else:
                self.itemconfig(self.arcs[index], start=start, extent=extent, fill=color)
            start+=extent


class ResizingLabel(TK.Label):
    def __init__(self,*args,**kwargs):
        TK.Label.__init__(self,*args,**kwargs)
        self.bind('<Configure>', self.handle_resize)

    def handle_resize(self,event):
        self['wraplength']=event.width


class NowAndNextUI(TK.Frame):
    """ TKInter main UI
    """
    def __init__(self,master):
        TK.Frame.__init__(self,master,padx=15, pady=10)
        self.pack(expand=TK.YES, fill=TK.BOTH)

        left_frame = TK.Frame(self, width=140, height=140)
        self.clock_face=TimerWidget(left_frame, width=140,height=140)
        self.clock_face.pack(side=TK.LEFT)
        left_frame.pack(side=TK.LEFT)

        right_frame=TK.Frame(self, width=280, height=140)
        self.next_label=ResizingLabel(right_frame,
            text='Awaiting data...',
            anchor=TK.NW,
            wraplength=300,
            justify=TK.LEFT)
        self.next_label.pack(side=TK.LEFT, expand=TK.YES, fill=TK.BOTH)
        right_frame.pack(side=TK.RIGHT, expand=TK.YES, fill=TK.BOTH)

        self.next_deadline=get_cursor()
        self.following=[]

    def refresh_canvas(self):
        """ Every second, update the display. """
        self.after(1000, self.refresh_canvas)
        time_now = get_cursor() # TODO this dependency should be injected
        time_to_the_minute = time_now-datetime.timedelta(seconds=time_now.second)
        if time_now.minute != self.previous_minute:
            self.previous_minute = time_now.minute

            ongoing, upcoming = refresh_database(time_now)
            lines = [time_to_the_minute.strftime(UI_DATE_FORMAT)]
            lines.extend(map(lambda ev: f'    {ev.subject}', ongoing ))

            if len(upcoming):
                self.next_deadline = upcoming[0].start
                lines.append(f'Next:\n    {upcoming[0].subject}')
                lines.extend(map(lambda ev: f'    +{int((ev.start-self.next_deadline).total_seconds() / 60)}m {ev.subject}', upcoming[1:]))

                # All except the first delay can be precalculated
                self.following=list(map( lambda pair: pair[1].start-pair[0].start, zip( upcoming[:-1],upcoming[1:] )))
            else:
                self.next_deadline = time_now + datetime.timedelta(3600)

            self.next_label.config(text='\n'.join(lines))

        self.clock_face.set_times( [ self.next_deadline - time_now ] + self.following )

    def mainloop(self):
        self.previous_minute = None
        self.after(10, self.refresh_canvas)
        self.master.mainloop()


if __name__ == "__main__":
    root = TK.Tk()
    app = NowAndNextUI(root)
    root.title('Now & Next')
    root.attributes('-topmost', 1)
    root.geometry(f'450x160')

    root.wm_attributes("-topmost", 1)
    app.mainloop()
