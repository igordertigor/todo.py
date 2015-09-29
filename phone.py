#!/usr/bin/env python
# -*- coding: utf-8 -*-

import gammu
import datetime

##############################################################################################################
# Cell phone interaction


class CellPhone(object):
    """A cell phone object that uses gammu to sychnronize the cell phones todo list"""
    def __init__(self):
        self.sm = gammu.StateMachine()
        self.sm.ReadConfig()
        self.sm.Init()
        self.tasklist = []
        self.__read_entries()

    def __read_entries(self):
        try:
            todo = self.sm.GetNextToDo(Start=True)
        except gammu.ERR_EMPTY:
            return
        self.tasklist.append(self.format_todo(todo))
        while True:
            loc = todo["Location"]
            try:
                todo = self.sm.GetNextToDo(Location=loc)
            except gammu.ERR_EMPTY:
                break
            self.tasklist.append(self.format_todo(todo))

    def format_todo(self, todo):
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

        taskstr = u"%s +%d " % (taskmsg, priority)
        if duedate is not None:
            taskstr += u"@%s" % (duedate.isoformat().split("T")[0],)
        return taskstr

    def write_entry(self, task, when):
        if when is None:
            hour = 12
        else:
            hour = int(when)
        if task.due is not None:
            year, month, day = task.due.split("-")
            entries = [{"Type": "ALARM_DATETIME",
                        "Value": datetime.datetime(day=int(day), year=int(year), month=int(month), hour=hour)}]
        else:
            entries = []
        entries.append({"Type": "TEXT",
                        "Value": "%s :%s" % (task.task, task.project)})
        newentry = {"Priority": "Medium",
                    "Type": "MEMO",
                    "Entries": entries}
        self.sm.AddToDo(newentry)
