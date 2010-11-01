#!/usr/bin/env python

import os,re,sys
import datetime

# Color settings

blackfg   = "30"
redfg     = "31"
greenfg   = "32"
yellowfg  = "33"
bluefg    = "34"
magentafg = "35"
cyanfg    = "36"
whitefg   = "37"
defaultfg = "39"

blackbg   = "40"
redbg     = "41"
greenbg   = "42"
yellowbg  = "43"
bluebg    = "44"
magentabg = "45"
cyanbg    = "46"
whitebg   = "47"
defaultbg = "49"

reset     = "0"
bold      = "1"
italics   = "3"
underline = "4"
strikethrough = "9"

# Other configuration
todofile = os.path.expanduser ( os.path.join ( "~", "todo.txt" ) )
donefile = os.path.expanduser ( os.path.join ( "~", "done.txt" ) )
criticaldays = 2
normalcolor = ";".join ( [reset,defaultfg,defaultbg] )
datecolors = [ normalcolor,";".join ( [reset,yellowfg] ), ";".join ( [reset,redfg,bold] ) ]
prioritycolors = [normalcolor,";".join([normalcolor,bold]),
        ";".join([reset,cyanfg]), ";".join([reset,cyanfg,bold]),
        ";".join([reset,magentafg]),";".join([reset,magentafg,bold]),
        ";".join([reset,yellowfg]),";".join([reset,yellowfg,bold]),
        ";".join([reset,redfg]),";".join([reset,redfg,bold])]
projectcolors = {}

##############################################################################################################

def parsetask ( task ):
    """Takes a task string and splits it up to task, due, priority and project information"""
    due,task = parsedue ( task )
    priority,task = parsepriority ( task )
    project,task = parseproject ( task )
    return task.strip(" \n"),due,priority,project

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

###############################################
# Actions
###############################################

def task_add ( opts, args ):
    """Add a task to the todo file.

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

    newtask = Task ( " ".join(args[1:]) )
    if not opts.dry:
        f = open ( todofile, 'a' )
        f.write ( str(newtask)+"\n" )
        f.close()
    elif opts.verbose:
        print str ( newtask )+"\n"

def task_ls ( opts, args ):
    """list tasks from the todo file

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

def task_done ( opts, args ):
    """remove tasks from todo.txt

    todo.py done [regexp]

    If called without arguments, this will delete all outdated tasks, otherwise it will delete all tasks with a message
    that matches the given regular expression. In almost any case, you will have to quote the regular expression.
    """
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
            if t.match ( " ".join(args[1:]) ):
                donetasks.append ( str(t) )
            else:
                todotasks.append ( str(t) )
        else:
            todotasks.append ( str(t) )

    if not opts.dry:
        f = open ( todofile, "w" )
        f.write ( "\n".join ( todotasks )+"\n" )
        f.close()
        f = open ( donefile, "w" )
        f.write ( "\n".join ( donetasks )+"\n")
        f.close()
    elif opts.verbose:
        print "TODO"
        print "\n".join ( todotasks )+"\n"
        print "\nDONE"
        print "\n".join ( donetasks )+"\n"

def task_update ( opts, args ):
    """update tasks

    todo.py update <regexp> <newattribute ...>

    Here, regexp has to be a regular expression (in most cases, you will have to quote it) and new
    attributes can be set using the +,:,@ markers
    """

    tasks = []
    f = open ( todofile )
    lines = f.readlines()
    f.close()
    for l in lines:
        tasks.append ( Task ( l ) )
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
        f = open ( todofile, "w" )
        f.write ( newtasks )
        f.close()
    elif opts.verbose:
        print newtasks

def task_merge ( opts, args ):
    """merge a 'todo' file with the default file

    todo.py merge <second file> [regexp]

    Merges the second file in the current todo file. If a regular expression is given, only those tasks form
    the second file are used that match the regular expression.
    """
    tasks = []
    f = open ( todofile )
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
        t = Task ( l )
        if t.match ( " ".join ( args[2:] ) ):
            tasks.append ( str(t) )
    if not opts.dry:
        f = open ( todofile, "w" )
        f.write ( "".join(tasks) )
        f.close ()
    elif opts.verbose:
        print "".join(tasks)

###############################################
# Task object
###############################################

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
    parser = OptionParser ( usage="""todo.py [options] <action> <arguments>

            Possible Actions
            ================

            help <action>                 more detailed help on an action
            add <task>                    add a task to the todo file
            ls <sorted by> [project]      list tasks sorted by a criterion
            done <regexp>                 remove tasks from the todo file
            update <task> [new setting]   modify a task
            merge <file> [regexp]         merge contents from another file
            """ )

    parser.add_option ( "-c", "--cfg", help="use config file other than the default ~/.config/todo/config",
            default=os.path.expanduser ( os.path.join ( "~",".config","todo","config" ) ) )
    parser.add_option ( "-d", "--dry", help="'dry run', i.e. all operations are performed but no files are actually written",
            action="store_true" )
    parser.add_option ( "-v", "--verbose", help="print status messages on try runs",
            action="store_true" )

    opts, args = parser.parse_args()

    try:
        execfile ( opts.cfg )
    except IOError:
        # Ignore configuration
        pass

    if args[0][0] == "h":
        if len(args)==1:
            parser.print_help()
        else:
            print eval ( "task_%s" % ( args[1], ) ).__doc__
    else:
        eval ( "task_%s" % ( args[0], ) )(opts,args)
