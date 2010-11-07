#!/usr/bin/env python
# -*- coding: utf-8 -*-
licensetext = u"""
     Managing todo text files from the command line
     Copyright (C) 2010  Ingo Fründ (ingo.fruend@googlemail.com)

     This program is free software; you can redistribute it and/or modify
     it under the terms of the GNU General Public License as published by
     the Free Software Foundation; either version 2 of the License, or
     (at your option) any later version.

     This program is distributed in the hope that it will be useful,
     but WITHOUT ANY WARRANTY; without even the implied warranty of
     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
     GNU General Public License for more details.

     You should have received a copy of the GNU General Public License
     along with this program; if not, write to the Free Software
     Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
"""

import os,re,sys
import datetime
import gammu

helptext = u"""

    todo.py [options] <action> <arguments>

            Possible Actions
            ================

            help <action>                 more detailed help on an action
            add <task>                    add a task to the todo file
            ls <sorted by> [project]      list tasks sorted by a criterion
            done <regexp>                 remove tasks from the todo file
            update <task> [new setting]   modify a task
            merge <file> [regexp]         merge contents from another file
            sync <get|regexp> [hour]      use gammu to synchronize with cell phone tasklist
"""
descriptiontext = u"""todo.py version 0.1, Copyright (C) 2010 Ingo Fründ
todo.py comes with ABSOLUTELY NO WARRANTY; for details type `todo.py help'.
This is free software, and you are welcome to redistribute it
under certain conditions; type `todo.py --license' for details.
"""

# Color settings
ansicolors = {"blackfg": "30",
        "redfg": "31",
        "greenfg": "32",
        "yellowfg": "33",
        "bluefg": "34",
        "magentafg": "35",
        "cyanfg": "36",
        "whitefg": "37",
        "defaultfg": "39",
        "blackbg": "40",
        "redbg": "41",
        "greenbg": "42",
        "yellowbg": "43",
        "bluebg": "44",
        "magentabg": "45",
        "cyanbg": "46",
        "whitebg": "47",
        "defaultbg": "49",
        "reset": "0",
        "bold": "1",
        "italics": "3",
        "underline": "4",
        "strikethrough": "9"}

##############################################################################################################

def parsetask ( task ):
    """Takes a task string and splits it up to task, due, priority and project information"""
    due,task = parsedue ( task )
    priority,task = parsepriority ( task )
    project,task = parseproject ( task )
    return unicode ( task.strip(" \n") ),due,priority,project

def parsedue ( task ):
    """Takes a due date match and converts it to an isoformatted date

    In particular, if a match was found, dates like +3d or +2w are interpreted as
    'in three days' or 'in two weeks'
    """
    mdue = re.search ( r"@([\d\-+wd]+)", task )
    task = re.sub ( r"(@[\d\-+wd]+)", "", task ).strip()

    if mdue is None:
        return None,task
    else:
        due = mdue.group(1)
    if due[0]=="+":
        # Add something to the current date
        if due[-1] == "w":
            due = str ( datetime.date.today() + datetime.timedelta ( days=7*int(due[1:-1]) ) )
        elif due[-1] == "d":
            due = str ( datetime.date.today() + datetime.timedelta ( days=int(due[1:-1]) ) )
        else:
            raise ValueError, "Unrecognized date modifier '%s'" % (due[-1],)
    else:
        due = parsedate ( due ).isoformat()
    return due,task

def parsepriority ( task ):
    """Determine priority from a priority match"""

    mpriority = re.search ( r"\+(\d)", task )
    task = re.sub ( r"(\+\d)", "", task )

    if mpriority is None:
        return 0, task
    if isinstance (mpriority, str ):
        return int ( mpriority )
    return int ( mpriority.group(1) ), task

def parseproject ( task ):
    """Determine project from a priority match"""

    mproject = re.search ( r"\:(\S*)", task )
    task = re.sub ( r"(\:\S*)", "", task )

    if mproject is None:
        return None,task
    elif isinstance ( mproject, str ):
        return mproject
    else:
        return mproject.group(1),task

def parsedate ( date ):
    """create a datatime.date from an isoformatted date string"""
    year,month,day = date.split("-")
    return datetime.date ( int(year), int(month), int(day) )

##############################################################################################################

def compare_by_date ( T1, T2 ):
    """Comparison function to compare two tasks by date (for sorting)"""
    # If one of the due dates is None, the due date is taken to be larger than everything else
    if T1.due is None:
        if T2.due is None:
            return 0
        else:
            return 1
    elif T2.due is None:
        return -1
    # Otherwise, we have to compare the dates
    D1 = parsedate ( T1.due )
    D2 = parsedate ( T2.due )
    if D1>D2:
        return 1
    elif D1==D2:
        return 0
    else:
        return -1

def compare_by_priority ( T1, T2 ):
    """Comparison function to compare two tasks by priority (for sorting)"""
    if T1.priority>T2.priority:
        return -1
    elif T1.priority==T2.priority:
        return 0
    else:
        return 1

def compare_by_project ( T1, T2 ):
    """Comparison function to compare two tasks by project"""
    # If one of the projects is none, the task comes last
    if T1.project is None:
        if T2.project is None:
            return 0
        else:
            return 1
    if T2.project is None:
        return -1
    # Otherwise, sort projects alphabetically
    if T1.project>T2.project:
        return 1
    elif T1.project==T2.project:
        return 0
    else:
        return -1

def check_due ( d, criticaldays ):
    """Check due date

    There are three possible due dates:
        2 => the task is overdue
        1 => the task will be due in <criticaldays> days
        0 => task task will not be due in the next days
    """
    if d.due is None:
        return 0
    D = parsedate ( d.due )
    if D<datetime.date.today():
        return 3
    elif D == datetime.date.today():
        return 2
    elif D-datetime.timedelta ( days=criticaldays ) < datetime.date.today():
        return 1
    else:
        return 0

def setcolor ( tasks, what ):
    """Set the coloring scheme for a list of tasks"""
    for t in tasks:
        t.coloring = what

##############################################################################################################
# Cell phone interaction

class CellPhone ( object ):
    """A cell phone object that uses gammu to sychnronize the cell phones todo list"""
    def __init__ ( self ):
        self.sm = gammu.StateMachine()
        self.sm.ReadConfig()
        self.sm.Init()
        self.tasklist = []
        self.__read_entries()
    def __read_entries ( self ):
        try:
            todo = self.sm.GetNextToDo ( Start=True )
        except gammu.ERR_EMPTY:
            return
        self.tasklist.append ( self.format_todo ( todo ) )
        while True:
            loc = todo["Location"]
            try:
                todo = self.sm.GetNextToDo ( Location=loc )
            except gammu.ERR_EMPTY:
                break
            self.tasklist.append ( self.format_todo ( todo ) )
    def format_todo( self, todo ):
        duedate = None
        taskmsg = ""
        for e in todo["Entries"]:
            if e["Type"] == "TEXT":
                taskmsg = e["Value"]
            elif e["Type"] == "ALARM_DATETIME":
                duedate = e["Value"]
        if todo["Priority"] == None:
            priority = 0
        elif todo["Priority"] == "Low":
            priority = 1
        elif todo["Priority"] == "Medium":
            priority = 2
        elif todo["Priority"] == "High":
            priority = 3

        return "%s @%s +%d" % ( taskmsg,duedate.isoformat().split("T")[0],priority )
    def write_entry ( self, task, when ):
        if when is None:
            hour = 12
        else:
            hour = int ( when )
        if not task.due is None:
            year,month,day = task.due.split("-")
            entries = [{"Type": "ALARM_DATETIME", "Value": datetime.datetime ( day=int(day), year=int(year), month=int(month), hour=hour )}]
        else:
            entries = []
        entries.append ( {"Type": "TEXT", "Value": "%s :%s" % ( task.task, task.project )} )
        newentry = {"Priority": "Medium", "Type": "MEMO",
                "Entries": entries }
        self.sm.AddToDo ( newentry )

###############################################
# Actions
###############################################

def task_add ( cfg,opts, args ):
    """
    Add a task to the todo file.

    todo.py add <task-message> [@due-date] [+priority] [:project]

    A task has to contain a message. In additon, three bits of information can be associated with a task:
       due-date      If a word in the task starts with '@', this word is taken as the due date. Due dates
                     can be specified as absolute dates (e.g. 2011-10-03 to denote the 3rd of October in 2010
                     or they can be specified as relative dates. Relative dates consist of a '+' sign, a number
                     and a unit. Valid units are 'd' for days and 'w' for weeks. That is +4d means the task is
                     due in 4 days, while +1w means the task is due in one week. By default, tasks have no due
                     date, which means you can postpone them infinitely long.
       priority      Tasks can be ranked by a one digit priority. To add a priority to a task, add an exclamation
                     mark '!' followed by a number to the task description. By default, all tasks have a priority
                     of 0.
       project       Tasks can be marked by project labels. Project labels should consist of a single word.
                     To mark a task as belonging to a project, simply add ':' followed by the project name
                     to the task specification.

    Examples
    --------

    todo.py add Think about version control for todo.py
            adds a task with the message "Think about version control for todo.py" to your todo file

    todo.py add Add more detailed documentation =todo.py
            adds a task with message "Add more detailed documentation" to your todo file and mark it as belonging
            to the project todo.py

    todo.py add Read a book @+3d
            adds a task with message "Read a book" to the todo file and mark it as "due in three days"

    todo.py add Call Walter +4
            adds a task with message "Call Walter" to the todo file and mark it as priority 4
    """
    newtask = Task ( " ".join(args[1:]), cfg )
    if not opts.dry:
        f = open ( cfg["todofile"], 'a' )
        f.write ( str(newtask)+"\n" )
        f.close()
    elif opts.verbose:
        print str ( newtask )+"\n"

def task_ls ( cfg, opts, args ):
    """
    list tasks from the todo file

    todo.py ls [<sorted by>]

    By default, tasks are listed in the same sequence as they are in the todo.txt file. If sorted by is assigned
    a value, they can also be sorted by other things:

    todo.py ls priority
            tasks are sorted by priority
    todo.py ls project
            tasks are sorted by project
    todo.py ls due
            tasks are sorted by due date

    If tasks are sorted, they are also colored accordingly.

    In addition, a single projects can be selected by adding a project argument (':' followed by project name)
    """

    tasks = []
    for l in open ( cfg["todofile"] ):
        tasks.append ( Task ( l, cfg ) )
    tasks.sort ( compare_by_priority )
    projects = []
    sortby = ""
    for a in args[1:]:
        if a[0] == ":":
            projects.append ( a[1:] )
        else:
            sortby = a
    if sortby == "":
        pass
    elif sortby[0] == "d":
        tasks.sort ( compare_by_date )
        setcolor ( tasks, 'date' )
    elif sortby[:3] == "pri":
        tasks.sort ( compare_by_priority )
        setcolor ( tasks, 'priority' )
    elif sortby[:3] == "pro":
        tasks.sort ( compare_by_project )
        setcolor ( tasks, 'project' )
    for t in tasks:
        if len(projects)==0 or t.project in projects:
            print t

def task_done ( cfg, opts, args ):
    """
    remove tasks from todo.txt

    todo.py done [regexp]

    If called without arguments, this will delete all outdated tasks, otherwise it will delete all tasks with a message
    that matches the given regular expression. In almost any case, you will have to quote the regular expression.
    """
    tasks = []
    f = open ( cfg["todofile"] )
    lines = f.readlines()
    f.close()
    for l in lines:
        tasks.append ( Task ( l, cfg ) )
    todotasks = []
    donetasks = []
    for t in tasks:
        if len(args)==1 and check_due(t,cfg["criticaldays"])==2:
            donetasks.append ( str(t) )
        elif len(args)==2:
            if t.match ( " ".join(args[1:]) ):
                donetasks.append ( str(t) )
            else:
                todotasks.append ( str(t) )
        else:
            todotasks.append ( str(t) )

    if not opts.dry:
        f = open ( cfg["todofile"], "w" )
        f.write ( "\n".join ( todotasks )+"\n" )
        f.close()
        f = open ( cfg["donefile"], "w" )
        f.write ( "\n".join ( donetasks )+"\n")
        f.close()
    elif opts.verbose:
        print "TODO"
        print "\n".join ( todotasks )+"\n"
        print "\nDONE"
        print "\n".join ( donetasks )+"\n"

def task_update ( cfg, opts, args ):
    """
    update tasks

    todo.py update <regexp> <newattribute ...>

    Here, regexp has to be a regular expression (in most cases, you will have to quote it) and new
    attributes can be set using the +,:,@ markers
    """

    tasks = []
    f = open ( cfg["todofile"] )
    lines = f.readlines()
    f.close()
    for l in lines:
        tasks.append ( Task ( l, cfg ) )
    ptrn = r"%s" % ( args[1], )
    for t in tasks:
        if t.match ( args[1] ):
            for m in args[2:]:
                if m[0] == "@":
                    t.due = parsedue ( m )[0]
                elif m[0] == ":":
                    t.project = parseproject ( m )[0]
                elif m[0] == "+":
                    t.priority = parsepriority ( m )[0]
    newtasks = "\n".join ( [ str(t) for t in tasks] ) + "\n"
    if not opts.dry:
        f = open ( cfg["todofile"], "w" )
        f.write ( newtasks )
        f.close()
    elif opts.verbose:
        print newtasks

def task_merge ( cfg, opts, args ):
    """
    merge a 'todo' file with the default file

    todo.py merge <second file> [regexp]

    Merges the second file in the current todo file. If a regular expression is given, only those tasks form
    the second file are used that match the regular expression.
    """
    tasks = []
    f = open ( cfg["todofile"] )
    lines = f.readlines()
    f.close()
    for l in lines:
        tasks.append ( l )
    f = open ( args[1] )
    lines = f.readlines()
    f.close()
    if len ( args ) > 2:
        ptrn = r"%s" % ( args[2] , )
    else:
        ptrn = r""
    for l in lines:
        t = Task ( l, cfg )
        if t.match ( " ".join ( args[2:] ) ):
            tasks.append ( str(t) )
    if not opts.dry:
        f = open ( cfg["todofile"], "w" )
        f.write ( "".join(tasks) )
        f.close ()
    elif opts.verbose:
        print "".join(tasks)

def task_sync ( cfg, opts, args ):
    """
    synchronize tasks with a mobile phone


    todo.py sync get

    Reads todo entries from a cell phone using gammu. These entries are then added to to configures todo.txt


    todo.py <regexp> [hour]

    writes entries selected by a regular expression to a cell phone using gammu. If an hour is specified, the
    cell phone's alarm is set to the particular hour. By default, the alarm will be set to noon if the task
    has a due date. Tasks that have no due date, will not have an alarm associated.
    """
    c = CellPhone()
    if args[1] == "get":
        newtasks = "\n".join ( [ str(Task ( t, cfg )) for t in c.tasklist ] ) + "\n"
        if not opts.dry:
            f = open ( cfg["todofile"], 'a' )
            f.write ( newtasks )
            f.close()
        elif opts.verbose:
            print str ( newtasks )
    else:
        # search for tasks that match the given pattern
        f = open ( cfg["todofile"] )
        lines = f.readlines ()
        f.close ()
        ptrn = r"%s" % ( args[1], )
        if len(args) > 2:
            when = args[2]
        else:
            when = None
        for l in lines:
            t = Task ( l, cfg )
            if t.match ( args[1] ):
                c.write_entry ( t, when )

###############################################
# Task object
###############################################

class Task ( object ):
    def __init__ ( self, message, cfg ):
        """Create a task from a string"""
        self.task,self.due,self.priority,self.project = parsetask ( message )
        self.coloring = ""
        self.datecolors = [cfg["duenormal"], cfg["duesoon"], cfg["duetoday"], cfg["dueover"]]
        self.prioritycolors = []
        for p in xrange ( 10 ):
            self.prioritycolors.append ( cfg["priority%d" % (p,)] )
        self.projectcolors = {}
        for p,c in cfg["projects"]:
            self.projectcolors[p] = c
        self.criticaldays = cfg["criticaldays"]
    def __str__ ( self ):
        msg = u""
        if not self.project is None:
            msg += u" :%s" % (self.project,)
        if len(msg) < 17:
            msg += u" " * ( 17-len(msg) )
        if not self.priority is None:
            msg += u" +%d" % (self.priority,)
        if not self.due is None:
            msg += u" @%s" % (self.due,)
        else:
            msg += u" "*12
        msg += u"   " + self.task
        if self.coloring=="date":
            msg = u"\033[" + self.datecolors[check_due(self,self.criticaldays)] + "m" + msg + "\033[" + ansicolors["reset"] + "m"
        elif self.coloring=="priority":
            msg = u"\033[" + self.prioritycolors[self.priority] + "m" + msg + "\033[" + ansicolors["reset"] + "m"
        elif self.coloring=="project":
            msg = u"\033[" + self.projectcolors.setdefault (self.project, ansicolors["reset"]) + "m" + msg + "\033[" + ansicolors["reset"] + "m"
        return msg.encode("utf-8")
    def match ( self, regexp, project=None ):
        """Does this task match a regular expression?"""
        if project is None:
            project,regexp = parseproject ( regexp )
        ptrn = r"%s" % ( regexp, )
        mtask = re.search ( ptrn.strip(), self.task ) is not None
        if project is None:
            mproject = True
        else:
            if self.project is None:
                mproject = project is None
            else:
                mproject = re.search ( r"%s" % (project), self.project ) is not None
        return mtask and mproject

if __name__ == "__main__":
    from optparse import OptionParser
    from ConfigParser import SafeConfigParser
    parser = OptionParser ( usage=helptext, description=descriptiontext )

    parser.add_option ( "-c", "--cfg", help="use config file other than the default ~/.config/todo/config",
            default=os.path.expanduser ( os.path.join ( "~",".config","todo","config" ) ) )
    parser.add_option ( "-d", "--dry", help="'dry run', i.e. all operations are performed but no files are actually written",
            action="store_true" )
    parser.add_option ( "-v", "--verbose", help="print status messages on try runs",
            action="store_true" )
    parser.add_option ( "-l", "--license", help="show license information and exit", action="store_true" )

    opts, args = parser.parse_args()

    if opts.license:
        print licensetext
        sys.exit ()

    cfgparser = SafeConfigParser ( )
    cfgparser.add_section ( "config" )
    cfgparser.add_section ( "due" )
    cfgparser.add_section ( "priority" )
    cfgparser.add_section ( "projects" )
    cfgparser.set ( "config", "todofile", "os.path.expanduser ( os.path.join ( '~', 'todo.txt' ) )" )
    cfgparser.set ( "config", "donefile", "os.path.expanduser ( os.path.join ( '~', 'done.txt' ) )" )
    cfgparser.set ( "config", "criticaldays", "2" )
    cfgparser.set ( "due", "normal", 'reset' )
    cfgparser.set ( "due", "soon",  'reset+";"+yellowfg' )
    cfgparser.set ( "due", "today", 'reset+";"+redfg' )
    cfgparser.set ( "due", "over",  'reset+";"+redfg+";"+bold' )
    cfgparser.set ( "priority", "p0", 'reset' )
    cfgparser.set ( "priority", "p1", 'reset+";"+bold' )
    cfgparser.set ( "priority", "p2", 'reset+";"+cyanfg' )
    cfgparser.set ( "priority", "p3", 'reset+";"+cyanfg+";"+bold' )
    cfgparser.set ( "priority", "p4", 'reset+";"+magentafg' )
    cfgparser.set ( "priority", "p5", 'reset+";"+magentafg+";"+bold' )
    cfgparser.set ( "priority", "p6", 'reset+";"+yellowfg' )
    cfgparser.set ( "priority", "p7", 'reset+";"+yellowfg+";"+bold' )
    cfgparser.set ( "priority", "p8", 'reset+";"+redfg' )
    cfgparser.set ( "priority", "p9", 'reset+";"+redfg+";"+bold' )

    cfgparser.read ( opts.cfg )

    config = {
            "todofile":  eval ( cfgparser.get ( "config", "todofile" ) ),
            "donefile":  eval ( cfgparser.get ( "config", "donefile" ) ),
            "criticaldays": cfgparser.getint ( "config", "criticaldays"),
            "duenormal": eval ( cfgparser.get ( "due", "normal" ), ansicolors ),
            "duesoon":   eval ( cfgparser.get ( "due", "soon" ),   ansicolors ),
            "duetoday":  eval ( cfgparser.get ( "due", "today" ),  ansicolors ),
            "dueover":   eval ( cfgparser.get ( "due", "over" ),   ansicolors ),
            "priority0": eval ( cfgparser.get ( "priority", "p0" ), ansicolors ),
            "priority1": eval ( cfgparser.get ( "priority", "p1" ), ansicolors ),
            "priority2": eval ( cfgparser.get ( "priority", "p2" ), ansicolors ),
            "priority3": eval ( cfgparser.get ( "priority", "p3" ), ansicolors ),
            "priority4": eval ( cfgparser.get ( "priority", "p4" ), ansicolors ),
            "priority5": eval ( cfgparser.get ( "priority", "p5" ), ansicolors ),
            "priority6": eval ( cfgparser.get ( "priority", "p6" ), ansicolors ),
            "priority7": eval ( cfgparser.get ( "priority", "p7" ), ansicolors ),
            "priority8": eval ( cfgparser.get ( "priority", "p8" ), ansicolors ),
            "priority9": eval ( cfgparser.get ( "priority", "p9" ), ansicolors ),
            "projects": []
            }
    for o in cfgparser.options ( "projects" ):
        config["projects"].append ( ( o, eval ( cfgparser.get ( "projects", o ), ansicolors ) ) )

    if args[0][0] == "h":
        if len(args)==1:
            parser.print_help()
        else:
            print eval ( "task_%s" % ( args[1], ) ).__doc__
    else:
        eval ( "task_%s" % ( args[0], ) )(config,opts,args)
