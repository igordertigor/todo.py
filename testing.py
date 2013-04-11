#!/usr/bin/env python

import unittest as ut
import datetime
import todo
import re

config = {
        "todofile":  "test_todo.txt",
        "donefile":  "test_done.txt",
        "criticaldays": 1,
        'duesoon': '0;33',
        'duetoday': '0;31',
        "duenormal": ' ',
        'dueover': '0;31;1',
        'priority0': '0',
        'priority1': '0;1',
        'priority2': '0;36',
        'priority3': '0;36;1',
        'priority5': '0;35;1',
        'priority4': '0;35',
        'priority6': '0;33',
        'priority7': '0;33;1',
        'priority8': '0;31',
        'priority9': '0;31;1',
        "ls_sortby":  "",
        "projects": []
        }

class TestParsers ( ut.TestCase ):
    def test_parsedue ( self ):
        self.assertEqual ( todo.parsedue ( " @2010-10-29" )[1], "" )
        self.assertEqual ( todo.parsedue ( " @2010-10-29" )[0], "2010-10-29" )
        targetday = (datetime.date.today()+datetime.timedelta ( days=7 )).isoformat ()
        self.assertEqual ( todo.parsedue ( " @+7d" )[0], targetday )
        self.assertEqual ( todo.parsedue ( " @+1w" )[0], targetday )
    def test_parsepriority ( self ):
        self.assertEqual ( todo.parsepriority ( "+1" )[1], "")
        self.assertEqual ( todo.parsepriority ( "+1" )[0], 1 )
        self.assertEqual ( todo.parsepriority ( "" )[0], 0 )
    def test_parseproject ( self ):
        self.assertEqual ( todo.parseproject ( ":test" )[0], "test" )
        self.assertEqual ( todo.parseproject ( "" )[0], None )
        self.assertEqual ( todo.parseproject ( ":test" )[1], "" )
    def test_parsedate ( self ):
        d = todo.parsedate ( "2010-10-29" )
        self.assertEqual ( d.year, 2010 )
        self.assertEqual ( d.month, 10 )
        self.assertEqual ( d.day, 29 )
    def test_parsetask ( self ):
        tsk = todo.parsetask ( "test" )
        self.assertEqual ( tsk, ("test",None,0,None) )
        tsk = todo.parsetask ( "test +4" )
        self.assertEqual ( tsk, ("test",None,4,None) )
        tsk = todo.parsetask ( "test @2010-10-29" )
        self.assertEqual ( tsk, ("test","2010-10-29",0,None) )
        tsk = todo.parsetask ( "test :dummy" )
        self.assertEqual ( tsk, ("test",None,0,"dummy") )
        tsk = todo.parsetask ( "test +4 @2010-10-29 :dummy" )
        self.assertEqual ( tsk, ("test","2010-10-29",4,"dummy") )

class TestTask ( ut.TestCase ):
    def test_TaskClass ( self ):
        T = todo.Task ( "test +4 @2010-10-29 :dummy", config )
        self.assertEqual ( T.task, "test" )
        self.assertEqual ( T.project, "dummy" )
        self.assertEqual ( T.priority, 4 )
        self.assertEqual ( T.due, "2010-10-29" )
        self.assertEqual ( str(T), " :dummy           +4 @2010-10-29   test" )
    def test_compare_by_priority (self):
        T1 = todo.Task ( "test +4", config )
        T2 = todo.Task ( "test +3", config )
        Tn = todo.Task ( "test", config )
        self.assertEqual ( todo.compare_by_priority ( T1, T2 ), -1 )
        self.assertEqual ( todo.compare_by_priority ( T1, T1 ), 0 )
        self.assertEqual ( todo.compare_by_priority ( T2, T1 ), 1 )
        self.assertEqual ( todo.compare_by_priority ( T1, Tn ), -1 )
        self.assertEqual ( todo.compare_by_priority ( Tn, T1 ), 1 )
        self.assertEqual ( todo.compare_by_priority ( Tn, Tn ), 0 )
    def test_compare_by_project ( self ):
        Ta = todo.Task ( "test :a", config )
        Tb = todo.Task ( "test :b", config )
        Tn = todo.Task ( "test", config )
        self.assertEqual ( todo.compare_by_project ( Ta, Tb ), -1 )
        self.assertEqual ( todo.compare_by_project ( Ta, Ta ), 0 )
        self.assertEqual ( todo.compare_by_project ( Tb, Ta ), 1 )
        self.assertEqual ( todo.compare_by_project ( Ta, Tn ), -1 )
        self.assertEqual ( todo.compare_by_project ( Tn, Ta ), 1 )
        self.assertEqual ( todo.compare_by_project ( Tn, Tn ), 0 )
    def test_compare_by_date ( self ):
        T0 = todo.Task ( "test @+0d", config )
        T1 = todo.Task ( "test @+1d", config )
        Tn = todo.Task ( "test", config )
        self.assertEqual ( todo.compare_by_date ( T0, T1 ), -1 )
        self.assertEqual ( todo.compare_by_date ( T0, T0 ), 0 )
        self.assertEqual ( todo.compare_by_date ( T1, T0 ), 1 )
        self.assertEqual ( todo.compare_by_date ( T0, Tn ), -1 )
        self.assertEqual ( todo.compare_by_date ( Tn, T0 ), 1 )
        self.assertEqual ( todo.compare_by_date ( Tn, Tn ), 0 )
    def test_check_due ( self ):
        T = todo.Task ( "test @+-1d", config )
        self.assertEqual ( todo.check_due ( T, 2 ), 3 )
        T = todo.Task ( "test @+0d", config )
        self.assertEqual ( todo.check_due ( T, 2 ), 2 )
        T = todo.Task ( "test @+1d", config )
        self.assertEqual ( todo.check_due ( T, 2 ), 1 )
        T = todo.Task ( "test @+2w", config )
        self.assertEqual ( todo.check_due ( T, 2 ), 0 )
        T = todo.Task ( "test", config )
        self.assertEqual ( todo.check_due ( T, 2 ), 0 )
    def test_setcolor ( self ):
        tasks = [todo.Task ( "test", config ), todo.Task ( "rest", config )]
        self.assertEqual ( tasks[0].coloring, "" )
        self.assertEqual ( tasks[1].coloring, "" )
        todo.setcolor ( tasks, "priority" )
        self.assertEqual ( tasks[0].coloring, "priority" )
        self.assertEqual ( tasks[1].coloring, "priority" )
    def test_match ( self ):
        T = todo.Task ( "this is a test", config )
        self.assertEqual ( T.match ( r"test" ), True )
        self.assertEqual ( T.match ( r"match" ), False )
        self.assertEqual ( T.match ( "rtest :ut" ), False )
        T = todo.Task ( "this is a test :ut", config )
        self.assertEqual ( T.match ( r"test", "ut" ), True )
        self.assertEqual ( T.match ( r"test" ), True )
        self.assertEqual ( T.match ( r"test :ut" ), True )
        self.assertEqual ( T.match ( r"match", "ut" ), False )
        self.assertEqual ( T.match ( r"match :ut" ), False )
        self.assertEqual ( T.match ( r"test :not" ), False )
        self.assertEqual ( T.match ( r"test", "not" ), False )
        self.assertEqual ( T.match ( r"match", "not" ), False )
        self.assertEqual ( T.match ( r"match :not" ), False )
        self.assertEqual ( T.match ( r"match", "ut" ), False )
        self.assertEqual ( T.match ( r"match :ut" ), False )
        self.assertEqual ( T.match ( r"test :not" ), False )
        self.assertEqual ( T.match ( r"test", "not" ), False )
        self.assertEqual ( T.match ( r"match", "not" ), False )
        self.assertEqual ( T.match ( r"match :not" ), False )

if __name__ == "__main__":
    ut.main()
