import gtk
import gedit
from simpletable import SimpleTable
from debugmodule import *

class Callstack (DebugModule):
    def __init__( self, window, plugin, debugger ):
        self.window = window
        self.plugin = plugin
        self.d = debugger

        self.panel = SimpleTable( (str, str, str), ('URI', 'Line', 'Function') )

        self.panel.connect( 'row-activated', self.jump_to_stack_signal )

        scrollbox = gtk.ScrolledWindow()
        scrollbox.add( self.panel )
        self.panel.show()

        stack_image = gtk.image_new_from_file( DebugModule.PLUGINPATH+'stack.png' )

        window.get_side_panel().add_item( scrollbox, 'Call Stack', stack_image )

    def jump_to_stack_signal(self, panel, path, column):
        v = self.panel[path[0]]
        uri = v[0]
        line = v[1]
        self.plugin.tabs.open_tab( uri, int(line) )

    def on_break(self, uri, line):
        self.panel.clear()
        self.d.request_callstack()

    def on_busy(self):
        self.panel.clear()

    def on_stopped(self):
        self.panel.clear()

    def on_callstack(self, callstack):
        self.panel.clear()
        for entry in callstack:
            print entry
            self.panel.append(entry)

    def state_changed(self, state):
        self.panel.clear()
