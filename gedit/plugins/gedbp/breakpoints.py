import gtk
import gedit
import gio
from simpletable import SimpleTable
from debugmodule import *

ui = """
<ui>
  <menubar name="MenuBar">
    <menu name="DebugMenu" action="Debug">
      <placeholder name="Debug">
        <menuitem action="SetBreakpoint"/>
      </placeholder>
    </menu>
  </menubar>

  <toolbar name="ToolBar">
    <placeholder name="Debug">
      <toolitem action="SetBreakpoint"/>
    </placeholder>
  </toolbar>
</ui>
"""

class Breakpoints (DebugModule):
    def __init__( self, window, plugin, debugger ):
        self.breakpoints = {} #(uri,line) -> (id, source_mark)
        self.window = window
        self.d = debugger
        self.plugin = plugin

        self.icon = gtk.gdk.pixbuf_new_from_file( DebugModule.PLUGINPATH+'bp.png' )
        image = gtk.image_new_from_pixbuf( self.icon )
        self.panel = SimpleTable( (str, str), ('URI', 'Line') )
        self.panel.connect( 'row-activated', self.jump_to_bp_signal )

        scrollbox = gtk.ScrolledWindow()
        scrollbox.add( self.panel )
        self.panel.show()
        window.get_side_panel().add_item( scrollbox, 'Breakpoints', image )

        actions = [
          ('SetBreakpoint', gtk.STOCK_NO, 'Set Breakpoint', 'F5', "Set Breakpoint", self.set_breakpoint_cb),
        ]

        action_group = gtk.ActionGroup("GDBpPluginActions")
        action_group.add_actions(actions)
        self.action = action_group.get_action('SetBreakpoint')

        manager = window.get_ui_manager()
        manager.insert_action_group(action_group, 0)

        ui_id = manager.add_ui_from_string(ui)

        self.SetBreakpointAction = action_group.get_action( "SetBreakpoint" )

    def project_created(self, project):
        self.plugin.project['breakpoints'] = []

    def project_loaded(self, project):
        print 'tabs: project_loaded'
        breakpoints = project['breakpoints'] # [(uri, line)]

        self.panel.clear()
        for bp in breakpoints:
            print 'append',bp
            self.panel.append( bp )
            tab = self.plugin.tabs.get_tab( bp[0] )
            mark = None
            if (tab != None) and (tab.get_state() == gedit.TAB_STATE_NORMAL):
                mark = self.show_breakpoint( tab.get_view(), bp[1] )
            self.breakpoints[bp] = (None, mark)

    def project_saving(self, project):
        for bp in self.breakpoints:
            project['breakpoints'].append( bp )

    def set_breakpoint_cb(self, action):
        self.toggle_breakpoint( self.window.get_active_view() )

    def prepare_view(self, view):
        view.set_mark_category_pixbuf( 'breakpoints', self.icon )
        view.set_mark_category_priority( 'breakpoints', 1 )
        buf = view.get_buffer()
        buf.connect( 'changed', self.buffer_changed_signal )

    def buffer_changed_signal(self, doc):
        docuri = doc.get_uri()
        for uri, line in self.breakpoints:
            if docuri != uri:
                continue

            id, mark = self.breakpoints[(uri, line)]
            if mark == None:
                continue
            iter_line = doc.get_iter_at_mark( mark ).get_line()+1
            print 'iter_line: ', iter_line

            if line != iter_line: #breakpoint was moved
                bp = self.breakpoints[(uri, line)]
                del self.breakpoints[(uri, line)]
                self.breakpoints[(uri, iter_line)] = bp

                idx = self.panel.find(uri, str(line))
                self.panel[idx] = (uri, iter_line)

    def jump_to_bp_signal(self, panel, path, column):
        v = panel[path[0]]
        uri = v[0]
        line = v[1]
        self.plugin.tabs.open_tab( uri, int(line) )

    def on_init(self, *params):
        idx = 0
        for uri, line in self.breakpoints:
            self.d.set_breakpoint( uri, line, idx )
            idx = idx + 1

    def on_breakpoint_mod(self, id, localid, state):
        bp = self.panel[localid]
        n, mark = self.breakpoints[(bp[0], int(bp[1]))]
        self.breakpoints[(bp[0], int(bp[1]))] = (id, mark)
        print self.breakpoints

    def show_breakpoint( self, view, line ):
        buf = view.get_buffer()
        bps = buf.get_source_marks_at_line( line-1, 'breakpoints' )

        if ( len(bps) == 0 ):
            i = buf.get_iter_at_line( line-1 )
            mark = buf.create_source_mark( None, 'breakpoints', i )
            return mark
        return bps[0]

    def hide_breakpoint( self, view, line ):
        buf = view.get_buffer()
        bps = buf.get_source_marks_at_line( line-1, 'breakpoints' )

        if ( len(bps) != 0 ):
            buf.delete_mark( bps[0] )

    def toggle_breakpoint(self, view):
        buf = view.get_property( 'buffer' )

        line = buf.get_iter_at_offset( buf.get_property( 'cursor-position' ) ).get_line()
        line += 1
        uri = buf.get_uri()

        bps = buf.get_source_marks_at_line( line-1, 'breakpoints' )

        if ( len(bps) == 0 ):
            mark = self.show_breakpoint( view, line )
            self.panel.append( (uri, line) )
            self.breakpoints[(uri, line)] = (None, mark)
            if ( self.plugin.state != DBGState.Idle ):
                self.d.set_breakpoint( uri, line, self.panel.length()-1 )
        else:
            self.hide_breakpoint( view, line )
            idx = self.panel.find(uri, str(line))
            if idx != None:
                self.panel.remove(idx)

            del self.breakpoints[(uri, line)]

            if ( self.plugin.state != DBGState.Idle ):
                self.d.remove_breakpoint( self.breakpoints[(uri, line)] )

    def on_tab_loaded(self, taburi, tab):
        print 'bp: on_tab_loaded'
        for uri, line in self.breakpoints:
            if uri == taburi:
                print 'our uri',uri
                mark = self.show_breakpoint( tab.get_view(), line )
                self.breakpoints[(uri, line)] = (None, mark)
