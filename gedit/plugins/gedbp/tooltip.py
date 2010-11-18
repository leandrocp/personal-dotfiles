import gtk
import gedit
from types import *
import sys
import random
from debugmodule import *

class Tooltip (DebugModule):
    def __init__( self, window, plugin, debugger ):
        self.window = window
        self.plugin = plugin
        self.d = debugger
        self.tooltip_prop = None

    def prepare_view(self, view):
        self.tooltip = gtk.Window( gtk.WINDOW_POPUP )
        self.tooltip.set_type_hint( gtk.gdk.WINDOW_TYPE_HINT_TOOLTIP )
        self.tooltip.set_name( 'gtk-tooltip' )
        self.ttlabel = gtk.Label( 'loading...' )
        self.ttlabel.show()
        self.tooltip.add( self.ttlabel )

        self.tooltip.connect( 'hide', self.tooltip_disappear_signal )
        self.tooltip.connect( 'show', self.tooltip_appear_signal )

        view.set_tooltip_window( self.tooltip )

        view.set_property( 'has-tooltip', True )
        view.connect( 'query-tooltip', self.query_tooltip_signal )

    def query_tooltip_signal(self, view, x, y, keyb, tooltip):
        if self.plugin.state != DBGState.Tracing:
            return False

        doc = view.get_buffer()

        if not doc.get_has_selection():
            return False

        bx, by = view.window_to_buffer_coords( gtk.TEXT_WINDOW_WIDGET, x, y )
        i = view.get_iter_at_location( bx, by )
        sel = doc.get_selection_bounds()
        if not i.in_range( *sel ):
            return False

        return True

    def tooltip_appear_signal(self, window):
        print 'tooltip appear',window

        view = self.window.get_active_tab().get_view()
        doc = view.get_buffer()
        sel = doc.get_selection_bounds()

        w = doc.get_text( *sel )

        self.tooltip_prop = random.randint( 0, sys.maxint )
        self.d.request_eval( self.tooltip_prop, w )

    def tooltip_disappear_signal(*params):
        print 'tooltip disappear',params

    def prop_to_string(self, prop, prefix=''):
        print 'prop_to_string:',prop
        res = prefix + str(prop[2])+' '+str(prop[0])+': '

        if type(prop[1]) == ListType:
            res += "\n"
            for p in prop[1]:
                res += prefix + self.prop_to_string( p, '    '+prefix ) + "\n"
        elif prop[1] == None:
            res += '<N/A>'
        else:
            res += '"'+prop[1]+'"'

        return res

    def update_tooltip(self, v):
        self.window.get_active_tab().get_view().get_tooltip_window().get_children()[0].set_text( self.prop_to_string( v ) )
#        self.ttlabel.set_text( str(v[2])+': "'+str(v[1])+'"' )
#       if you know why second line is not working please email me: thesame.ml@gmail.com

    def on_evaluated(self, localid, prop):
        print 'eval', localid
        if self.tooltip_prop == localid:
            print 'got tooltip'
            self.update_tooltip( prop )
