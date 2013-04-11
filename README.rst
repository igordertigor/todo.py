todo.py
=======
... is a simple python script that allows you to manage text-file todo lists

todo.py supports the following features:

    * Add tasks
    * print tasks sorted by different properties
    * moving tasks to a "done" file by regular expression
    * update tasks
    * merge task lists
    * synchronize tasks with your cell phone using gammu

See license file for license information.

.. include:: isonum.txt

Copyright |copy| 2013 by Ingo Fründ


Combining todo.py with the awesome window manager
=================================================

If you use `awesome <http://awesome.naquadah.org/>`_ as your window manager,
you might want to use todo.py directly from anywhere in your work.  Here is how
to configure <modkey>+<t> to prompt for a todo.py command:

Type if you use awesome with the default configuration, you can type

vim ~/.config/awesome/rc.lua +/"mypromptbox\[mouse\.screen\]:run()"

to jump to the configuration of the "Run:" prompt. We now generate a second prompt for todo.py by adding
the following lines::

    awful.key({ modkey },            "t",
              function ()
                  awful.prompt.run({ prompt = "todo "},
                  mypromptbox[mouse.screen].widget,
                  function (cmd) awful.util.spawn ( string.format ( "path/to/todo.py %s", cmd ) ) end,
                  nil,
                  nil )
              end),

where you should replace 'path/to/todo.py' by the path to your todo.py executable.
