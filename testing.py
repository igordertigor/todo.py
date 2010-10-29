#!/usr/bin/env python

import unittest as ut
import datetime
import todo
import re

class TestParsers ( ut.TestCase ):
    def test_parsedue ( self ):
        self.assertEqual ( todo.parsedue ( "2010-10-29" ), "2010-10-29" )
        targetday = (datetime.date.today()+datetime.timedelta ( days=7 )).isoformat ()
        self.assertEqual ( todo.parsedue ( "+7d" ), targetday )
        self.assertEqual ( todo.parsedue ( "+1w" ), targetday )
        m = re.search ( r"@(.*)", "@2010-10-29" )
        self.assertEqual ( todo.parsedue ( m ), "2010-10-29" )
        m = re.search ( r"@(.*)", "@+7d" )
        self.assertEqual ( todo.parsedue ( m ), targetday )
        m = re.search ( r"@(.*)", "@+1w" )
        self.assertEqual ( todo.parsedue ( m ), targetday )
        self.assertEqual ( todo.parsedue ( None ), None )
    def test_parsepriority ( self ):
        self.assertEqual ( todo.parsepriority ( "1" ), 1 )
        self.assertEqual ( todo.parsepriority ( None ), 0 )
        m = re.search ( r"\+(\d)", "+2" )
        self.assertEqual ( todo.parsepriority ( m ), 2 )
    def test_parseproject ( self ):
        self.assertEqual ( todo.parseproject ( "test" ), "test" )
        self.assertEqual ( todo.parseproject ( None ), None )
        m = re.search ( r":(.*)", ":test" )
        self.assertEqual ( todo.parseproject ( m ), "test" )
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
        T = todo.Task ( "test +4 @2010-10-29 :dummy" )
        self.assertEqual ( T.task, "test" )
        self.assertEqual ( T.project, "dummy" )
        self.assertEqual ( T.priority, 4 )
        self.assertEqual ( T.due, "2010-10-29" )
        self.assertEqual ( str(T), " :dummy           +4 @2010-10-29   test" )
    def test_compare_by_priority (self):
        T1 = todo.Task ( "test +4" )
        T2 = todo.Task ( "test +3" )
        Tn = todo.Task ( "test" )
        self.assertEqual ( todo.compare_by_priority ( T1, T2 ), -1 )
        self.assertEqual ( todo.compare_by_priority ( T1, T1 ), 0 )
        self.assertEqual ( todo.compare_by_priority ( T2, T1 ), 1 )
        self.assertEqual ( todo.compare_by_priority ( T1, Tn ), -1 )
        self.assertEqual ( todo.compare_by_priority ( Tn, T1 ), 1 )
        self.assertEqual ( todo.compare_by_priority ( Tn, Tn ), 0 )
    def test_compare_by_project ( self ):
        Ta = todo.Task ( "test :a" )
        Tb = todo.Task ( "test :b" )
        Tn = todo.Task ( "test" )
        self.assertEqual ( todo.compare_by_project ( Ta, Tb ), -1 )
        self.assertEqual ( todo.compare_by_project ( Ta, Ta ), 0 )
        self.assertEqual ( todo.compare_by_project ( Tb, Ta ), 1 )
        self.assertEqual ( todo.compare_by_project ( Ta, Tn ), -1 )
        self.assertEqual ( todo.compare_by_project ( Tn, Ta ), 1 )
        self.assertEqual ( todo.compare_by_project ( Tn, Tn ), 0 )
    def test_compare_by_date ( self ):
        T0 = todo.Task ( "test @+0d" )
        T1 = todo.Task ( "test @+1d" )
        Tn = todo.Task ( "test" )
        self.assertEqual ( todo.compare_by_date ( T0, T1 ), -1 )
        self.assertEqual ( todo.compare_by_date ( T0, T0 ), 0 )
        self.assertEqual ( todo.compare_by_date ( T1, T0 ), 1 )
        self.assertEqual ( todo.compare_by_date ( T0, Tn ), -1 )
        self.assertEqual ( todo.compare_by_date ( Tn, T0 ), 1 )
        self.assertEqual ( todo.compare_by_date ( Tn, Tn ), 0 )
    def test_check_due ( self ):
        T = todo.Task ( "test @+-1d" )
        self.assertEqual ( todo.check_due ( T ), 2 )
        T = todo.Task ( "test @+1d" )
        self.assertEqual ( todo.check_due ( T ), 1 )
        T = todo.Task ( "test @+2w" )
        self.assertEqual ( todo.check_due ( T ), 0 )
        T = todo.Task ( "test" )
        self.assertEqual ( todo.check_due ( T ), 0 )
    def test_setcolor ( self ):
        tasks = [todo.Task ( "test" ), todo.Task ( "rest" )]
        self.assertEqual ( tasks[0].coloring, "" )
        self.assertEqual ( tasks[1].coloring, "" )
        todo.setcolor ( tasks, "priority" )
        self.assertEqual ( tasks[0].coloring, "priority" )
        self.assertEqual ( tasks[1].coloring, "priority" )

if __name__ == "__main__":
    ut.main()
