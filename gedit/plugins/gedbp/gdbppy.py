import gtk
import gedit
import gtksourceview2 as gsrc
import gtk.glade
import dbgp
import string
import pickle
from simpletable import SimpleTable
from tabs import Tabs
from breakpoints import Breakpoints
from watches import Watches
from context import Context
from callstack import Callstack
from tooltip import Tooltip
from project import *
from debugmodule import *

ui_str = """
<ui>
  <menubar name="MenuBar">
    <menu name="FileMenu" action="File">
      <placeholder name="ProjectActs" position="top">
        <separator/>
        <menuitem action="NewProject"/>
        <menuitem action="LoadProject"/>
        <menuitem action="SaveProject"/>
        <menuitem action="SaveProjectAs"/>
        <separator/>
        <menuitem action="CloseProject"/>
        <separator/>
      </placeholder>
    </menu>

    <menu name="DebugMenu" action="Debug">
      <placeholder name="Debug">
        <menuitem action="Run"/>
        <menuitem action="StepInto"/>
        <menuitem action="StepOver"/>
        <menuitem action="Stop"/>
      </placeholder>
    </menu>
  </menubar>

  <toolbar name="ToolBar">
    <placeholder name="Debug">
      <toolitem action="Run"/>
      <toolitem action="StepInto"/>
      <toolitem action="StepOver"/>
      <toolitem action="StepOut"/>
      <toolitem action="Stop"/>
      <toolitem action="Test"/>
    </placeholder>
  </toolbar>
</ui>
"""

class DBGState:
    Idle = 0 #debugger is off
    Starting = 1
    Running = 2
    Tracing = 3
    Stopping = 4

class EventPriority:
    Normal = 0
    First = 1
    Last = 2
    Firstmost = 3
    Lastmost = 4

class Disp:
    def __init__(self, name, subscribers):
        self.name = name
        self.s = subscribers

    def __call__(self, *params):
        print 'Invoking',self.name
        tmp = "dest.%s(*params)" % self.name
        print tmp
        for dest in self.s:
            exec tmp

class DispatcherException (Exception):
    pass

class Dispatcher:
    def __init__(self):
        self.normal = []
        self.first = []
        self.last = []
        self.firstmost = None
        self.lastmost = None
        self.queue = []

    def add_subscriber(self, subscriber, prio=EventPriority.Normal):
        if prio == EventPriority.Normal:
            self.normal.append( subscriber )

        elif prio == EventPriority.First:
            self.first.append( subscriber )

        elif prio == EventPriority.Last:
            self.last.append( subscriber )

        elif prio == EventPriority.Firstmost:
            if self.firstmost == None:
                self.firstmost = subscriber
            else:
                raise DispatcherException, "Firstmost handler is already set to "+str(self.firstmost)

        elif prio == EventPriority.Lastmost:
            if self.lastmost == None:
                self.lastmost = subscriber
            else:
                raise DispatcherException, "Lastmost handler is already set to "+str(self.lastmost)

        self.queue = []
        if self.firstmost != None:
            self.queue.append( self.firstmost )
        self.queue.extend( self.first )
        self.queue.extend( self.normal )
        self.queue.extend( self.last )
        if self.lastmost != None:
            self.queue.append( self.lastmost )

    def __getattr__(self, name):
        return Disp( name, self.queue )

class GDBpPlugin (gedit.Plugin, EventSubscriber):
    def __init__(self):
        super(GDBpPlugin, self).__init__()
        self.eip_mark = None
        self.eip = None
        self.eip_img = gtk.gdk.pixbuf_new_from_file( PLUGINPATH+'eip.png' )
        self.dispatcher = Dispatcher()
        self.dispatcher.add_subscriber( self, EventPriority.Lastmost )
        self.state = DBGState.Idle
        DebugModule.PLUGINPATH = PLUGINPATH

    def set_state(self, state):
        self.state = state
        can_trace = ( state == DBGState.Tracing )
        if ( self.RunAction == None ):
            return

        for widget in self.active_widgets:
            widget.set_sensitive( can_trace )

        if ( not can_trace ):
            self.show_eip( None )

    def prepare_view(self, view):
        view.set_mark_category_pixbuf( 'eip', self.eip_img )
        view.set_mark_category_priority( 'eip', 2 )
        view.set_property( 'show-line-marks', True )

    def show_eip(self, *params):
        if ( self.eip_mark != None ):
            self.eip_mark.get_buffer().delete_mark( self.eip_mark )
            self.eip_mark = None

        if (params[0] == None):
            return

        view, line = params
        line -= 1
        buf = view.get_property( 'buffer' )
        marks = buf.get_source_marks_at_line( line, 'eip' )

        if ( len(marks) == 0 ):
            i = buf.get_iter_at_line( line )
            self.eip_mark = buf.create_source_mark( None, 'eip', i )
            view.scroll_to_mark( self.eip_mark, 0.1, False )

    def run_cb(self, action, window):
        self.set_state( DBGState.Running )
        self.d.run()
        print 'Run!'

    def step_into_cb(self, action, window):
        self.set_state( DBGState.Running )
        self.d.step_into()
        print 'Step Into'

    def step_over_cb(self, action, window):
        self.set_state( DBGState.Running )
        self.d.step_over()

    def step_out_cb(self, action, window):
        self.set_state( DBGState.Running )
        self.d.step_over()

    def stop_cb(self, action, window):
        self.d.stop()

    def test_cb(self, action, window):
        pass

    def new_project_cb(self, action, window):
        pass

    def load_project_cb(self, action, window):
        dialog = gtk.FileChooserDialog('Choose project file name', self.window, gtk.FILE_CHOOSER_ACTION_SAVE, (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK) )
        res = dialog.run()
        if res == gtk.RESPONSE_OK:
            filename = dialog.get_filename()
            dialog.destroy()
            try:
                self.project.load( filename )
            except:
                gtk.MessageDialog( self.window, gtk.DIALOG_MODAL, gtk.MESSAGE_ERROR, gtk.BUTTONS_OK, 'Failed to load project' )
                return
            self.config['last_project'] = filename

    def save_project_cb(self, action, window):
        try:
            self.project.save()
        except ProjectException:
            dialog = gtk.FileChooserDialog('Choose project file name', self.window, gtk.FILE_CHOOSER_ACTION_OPEN, (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_SAVE, gtk.RESPONSE_OK) )
            dialog.set_default_response( gtk.RESPONSE_OK )
            res = dialog.run()
            if res == gtk.RESPONSE_OK:
                filename = dialog.get_filename()
                self.project.save( filename )
                self.config['last_project'] = filename
            dialog.destroy()

    def save_project_as_cb(self, action, window):
        dialog = gtk.FileChooserDialog('Choose project file name', self.window, gtk.FILE_CHOOSER_ACTION_OPEN, (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_SAVE, gtk.RESPONSE_OK) )
        dialog.set_default_response( gtk.RESPONSE_OK )
        res = dialog.run()
        if res == gtk.RESPONSE_OK:
            filename = dialog.get_filename()
            self.project.save( filename )
            self.config['last_project'] = filename
        dialog.destroy()

    def close_project_cb(self, action, window):
        pass

    def init_ui(self, window):
        actions = [
          ('Debug', None, 'Debug'),
          ('Project', None, 'Project'),
          ('Run', gtk.STOCK_GOTO_LAST, 'Run', '<Ctrl>F9', "Run", self.run_cb),
          ('StepInto', gtk.STOCK_GO_FORWARD, 'Step Into', '<Ctrl>F7', "Step Into", self.step_into_cb),
          ('StepOver', gtk.STOCK_GO_FORWARD, 'Step Over', '<Ctrl>F6', "Step Over", self.step_over_cb),
          ('StepOut', gtk.STOCK_GO_UP, 'Step Out', '<Ctrl>F8', "Step Out", self.step_over_cb),
          ('Test', None, 'Test', '', "Test", self.test_cb),
          ('Stop', gtk.STOCK_STOP, 'Stop', '<Ctrl>F2', "Stop", self.stop_cb),

          ('NewProject', gtk.STOCK_NEW, 'New Project', '', "New Project", self.new_project_cb),
          ('SaveProject', gtk.STOCK_SAVE, 'Save Project', '', "Save Project", self.save_project_cb),
          ('SaveProjectAs', gtk.STOCK_SAVE_AS, 'Save Project As...', '', "Save Project As...", self.save_project_as_cb),
          ('LoadProject', gtk.STOCK_OPEN, 'Load Project', '', "Load Project", self.load_project_cb),
          ('CloseProject', gtk.STOCK_CLOSE, 'Close Project', '', "Close Project", self.close_project_cb)
        ]

        action_group = gtk.ActionGroup("GDBpPluginActions")
        action_group.add_actions(actions, window)

        self.RunAction = action_group.get_action( "Run" )
        self.StepIntoAction = action_group.get_action( "StepInto" )
        self.StepOverAction = action_group.get_action( "StepOver" )
        self.StepOutAction = action_group.get_action( "StepOut" )
        self.StopAction = action_group.get_action( "Stop" )

        manager = window.get_ui_manager()
        manager.insert_action_group(action_group, 0)

        ui_id = manager.add_ui_from_string(ui_str)
        debug_menu = manager.get_widget('/ui/MenuBar/DebugMenu')

#        manager.get_widget('/ui/MenuBar').reorder_child( debug_menu, 3 )
        print manager.get_widget('/ui/MenuBar')

        self.active_widgets = ( self.RunAction, self.StopAction, self.StepIntoAction, self.StepOverAction, self.StepOutAction )

    def on_connect(self):
        print 'connect'

    def on_init(self, *params):
        print 'init'
        '''
        prompt = gtk.Label( "Debugger is going to debug %s" % params[6] )

        dialog = gtk.Dialog( "Incoming debug request", self.window, gtk.DIALOG_MODAL,
            ( "Run", gtk.RESPONSE_OK,
            "Break", gtk.RESPONSE_APPLY,
            "Skip", gtk.RESPONSE_CANCEL ) )
        dialog.vbox.pack_start( prompt )
        resp = dialog.run()
        dialog.destroy()

        if ( resp == gtk.RESPONSE_OK ):
            self.d.run()
        elif ( resp == gtk.RESPONSE_APPLY ):
            self.d.step_into()
        elif ( resp == gtk.RESPONSE_CANCEL ):
            return False
        '''
        self.d.run()
#        self.d.step_into()
        return True

    def on_break(self, uri, line):
        self.set_state( DBGState.Tracing )

        print "Break at %s:%d" % (uri, line)
        self.eip = (uri, line)

        tab = self.tabs.open_tab(uri, line)
        if tab != None:
            self.show_eip( tab.get_view(), line )
        else:
            self.d.request_source( uri )

    def on_stopped(self):
        self.set_state( DBGState.Idle )

    def on_stopping(self):
        self.set_state( DBGState.Stopping )
        self.d.stop()

    def init_debugger(self):
        self.d = dbgp.dbgp( 'localhost', 9000, self.dispatcher )
#        self.d.on_init = self.on_init
        self.d.start()

    def on_tab_loaded( self, taburi, tab ):
        self.dispatcher.prepare_view( tab.get_view() )
        if ( self.eip != None and self.state != DBGState.Idle ):
            uri, line = self.eip
            if ( taburi == uri ):
                self.show_eip( tab.get_view(), line )

    def load_config(self):
        try:
            f = open( 'gedit-dbg.cfg', 'r' )
            self.config = pickle.load( f )
        except:
            self.config = {}

    def activate(self, window):
        self.load_config()

        self.init_debugger()

        self.project = Project( self.dispatcher )

        self.tabs = Tabs( window, self, self.dispatcher )

        self.window = window
        self.init_ui(window)

        self.module_names = [ 'Breakpoints', 'Watches', 'Context', 'Callstack', 'Tooltip' ]
        self.modules = {}

        for module in self.module_names:
            field = module.lower()
            exec "self.modules[\'%s\'] = %s( window, self, self.d )" % (field, module)
            exec "self.dispatcher.add_subscriber( self.modules['%s'] )" % field

        for view in window.get_views():
            self.dispatcher.prepare_view(view)

        try:
            print 'Loading',self.config['last_project']
            self.project.load( self.config['last_project'] )
        except:
            print 'failed'
            self.project.new()

        self.window.set_title( 'test' )

        self.set_state( DBGState.Idle )

    def save_config(self):
        try:
            f = open( 'gedit-dbg.cfg', 'w' )
            pickle.dump( self.config, f )
        except:
            print 'Warning: could not save config'

    def deactivate(self, window):
        self.save_config()
        if self.state != DBGState.Idle:
            self.d.stop()
        try:
            self.project.save()
        except:
            print 'Warinig: could not save project'
#        handlers = window.get_data(self.WINDOW_DATA_KEY)
#        for handler_id in handlers:
#            window.disconnect(handler)
#        window.set_data(self.WINDOW_DATA_KEY, None)

#        for view in window.get_views():
#            self.remove_helper(view)

    def update_ui(self, window):
        pass
