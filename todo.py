#!/usr/bin/env python

import os,re,sys
import datetime

# Color settings

redfg     = "31"
whitefg   = "37"
yellowfg  = "33"
magentafg = "35"
cyanfg    = "36"
bluefg    = "34"
bg        = "0;40"

bold      = "1"

# Other configuration
todofile = os.path.expanduser ( os.path.join ( "~", "todo.txt" ) )
donefile = os.path.expanduser ( os.path.join ( "~", "done.txt" ) )
criticaldays = 2
normalcolor = bg + ";" + whitefg
datecolors = [normalcolor,bg+";"+yellowfg,bg+";"+redfg]
prioritycolors = [normalcolor,normalcolor,bg+";"+cyanfg,bg+";"+cyanfg,bg+";"+magentafg,bg+";"+magentafg,
        bg+";"+yellowfg,bg+";"+yellowfg,bg+";"+redfg,bg+";"+redfg]
projectcolors = {}



def parsetask ( task ):
    """Takes a task string and splits it up to task, due, priority and project information"""
    mdue = re.search ( r" @(\S*)", task )
    task = re.sub ( r"( @\S*)", "", task )
    mpriority = re.search ( r" \+(\d)", task )
    task = re.sub ( r"( \+\d)", "", task )
    mproject = re.search ( r"\:(\S*)", task )
    task = re.sub ( r"(\:\S*)", "", task )
    due = parsedue ( mdue )
    priority = parsepriority ( mpriority )
    project = parseproject ( mproject )
    return task.strip(" \n"),due,priority,project

def parsedue ( mdue ):
    """Takes a due date match and converts it to an isoformatted date
    
    In particular, if a match was found, dates like +3d or +2w are interpreted as
    'in three days' or 'in two weeks'
    """
    if mdue is None:
        return None
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
    return due

def parsepriority ( mpriority ):
    """Determine priority from a priority match"""
    if mpriority is None:
        return 0
    return int ( mpriority.group(1) )

def parseproject ( mproject ):
    """Determine project from a priority match"""
    if mproject is None:
        return None
    else:
        return mproject.group(1)

def parsedate ( date ):
    """create a datatime.date from an isoformatted date string"""
    year,month,day = date.split("-")
    return datetime.date ( int(year), int(month), int(day) )

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

def check_due ( d ):
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
        return 2
    elif D-datetime.timedelta ( criticaldays ) < datetime.date.today():
        return 1
    else:
        return 0

def setcolor ( tasks, what ):
    """Set the coloring scheme for a list of tasks"""
    for t in tasks:
        t.coloring = what

class Task ( object ):
    def __init__ ( self, message ):
        """Create a task from a string"""
        self.task,self.due,self.priority,self.project = parsetask ( message )
        self.coloring = ""
    def __str__ ( self ):
        msg = ""
        if not self.project is None:
            msg += " :%s" % (self.project,)
        if len(msg) < 17:
            msg += " " * ( 17-len(msg) )
        if not self.priority is None:
            msg += " +%d" % (self.priority,)
        if not self.due is None:
            msg += " @%s" % (self.due,)
        else:
            msg += " "*12
        msg += "   " + self.task
        if self.coloring=="date":
            msg = "\033[" + datecolors[check_due(self)] + "m" + msg + "\033[" + normalcolor + "m"
        elif self.coloring=="priority":
            msg = "\033[" + prioritycolors[self.priority] + "m" + msg + "\033[" + normalcolor + "m"
        elif self.coloring=="project":
            msg = "\033[" + projectcolors.setdefault (self.project, normalcolor ) + "m" + msg + "\033[" + normalcolor + "m"
        return msg

# tasks = [Task ( "Work @+3d !1" ), Task ( "Write paper @+5d !2" ), Task ( "2nd derivative operator =psignifit" ), Task("Pack records !2"), Task("check rkd problems =psignifit !1"), Task("Something overdue @2010-10-28"), Task("Say hello to Hannah @2010-10-29")]
# 
# tasks.sort ( compare_by_priority )
# 
# print "\nsorted by priority"
# for t in tasks:
#     print t
# 
# tasks.sort ( compare_by_date )
# print "\nsorted by due date"
# for t in tasks:
#     print t
# 
# tasks.sort ( compare_by_project )
# setcolor(tasks, "project" )
# print "\nsorted by project"
# for t in tasks:
#     print t
# 

if __name__ == "__main__":
    from optparse import OptionParser
    parser = OptionParser ( usage="""todo.py [options] <action> <arguments>
            
            Possible Actions
            ================

            help <action>   more detailed help on an action
            add <task>      add a task to the todo file
            ls <sorted by>  list tasks sorted by a criterion
            done <task>     remove a task from the todo file
            """ )

    parser.add_option ( "-c", "--cfg", help="use config file other than the default ~/.config/todo/config",
            default=os.path.expanduser ( os.path.join ( "~",".config","todo","config" ) ) )

    opts, args = parser.parse_args()

    try:
        execfile ( opts.cfg )
    except IOError:
        # Ignore configuration
        pass

    if args[0] == "help":
        if len(args)==1:
            parser.print_help()
        elif args[1] == "add":
            print """Add a task to the todo file.

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
        elif args[1] == "ls":
            print """list tasks from the todo file

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
        elif args[1] == "done":
            print """remove tasks from todo.txt

            todo.py done [regexp]

            If called without arguments, this will delete all outdated tasks, otherwise it will delete all tasks with a message
            that matches the given regular expression. In almost any case, you will have to quote the regular expression.
            """

    elif args[0] == "add":
        if len(args)==1:
            parser.print_help()
        else:
            newtask = Task ( " ".join(args[1:]) )
            f = open ( todofile, 'a' )
            f.write ( str(newtask)+"\n" )
            f.close()
    elif args[0] == "ls":
        tasks = []
        for l in open ( todofile ):
            tasks.append ( Task ( l ) )
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
    elif args[0] == "done":
        tasks = []
        f = open ( todofile )
        lines = f.readlines()
        f.close()
        for l in lines:
            tasks.append ( Task ( l ) )
        todotasks = []
        donetasks = []
        for t in tasks:
            if len(args)==1 and check_due(t)==2:
                donetasks.append ( str(t) )
            elif len(args)==2:
                regex = r"%s" % ( args[1], )
                m = re.search ( regex, t.task )
                if not m is None:
                    donetasks.append ( str(t) )
                else:
                    todotasks.append ( str(t) )
            else:
                todotasks.append ( str(t) )

        f = open ( todofile, "w" )
        f.write ( "\n".join ( todotasks ) )
        f.close()
        f = open ( donefile, "w" )
        f.write ( "\n".join ( donetasks ) )
        f.close()
