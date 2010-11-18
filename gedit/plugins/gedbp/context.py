import gtk
import gedit
from types import *
import sys
import random
from propertymodel import PropertyModel
from debugmodule import *

class Context (DebugModule):
    def __init__(self, window, plugin, debugger ):
        self.window = window
        self.plugin = plugin
        self.d = debugger

        self.store = PropertyModel( self )
        self.panel = gtk.TreeView()
        self.panel.set_property('sensitive', False)
        self.panel.set_model( self.store )

        col = gtk.TreeViewColumn( 'Item', gtk.CellRendererText(), text=0, foreground=4 )
        col.set_resizable( True )
        self.panel.append_column( col )

        col = gtk.TreeViewColumn( 'Value', gtk.CellRendererText(), text=1, foreground=4 )
        col.set_resizable( True )
        self.panel.append_column( col )

        col = gtk.TreeViewColumn( 'Type', gtk.CellRendererText(), text=2, foreground=4 )
        col.set_resizable( True )
        self.panel.append_column( col )

        scrollbox = gtk.ScrolledWindow()
        scrollbox.add( self.panel )
        self.panel.show()
        window.get_side_panel().add_item( scrollbox, 'Context', gtk.image_new_from_file( DebugModule.PLUGINPATH+'context.png' ) )

        self.my_props = []

    def on_property_got(self, prop, localid):
        try:
            self.my_props.index( localid )
        except:
            return
        self.my_props.remove( localid )
        self.store.data_arrive( prop )
        self.restore_expanded()

    def request_property(self, prop):
        if prop == None:
            self.d.request_contexts()
        else:
            for idx in range(len(self.contexts)):
                name, id = self.contexts[idx]
                if name == prop:
                    self.d.request_context( id, idx )
                    return

            prop_id = random.randint( 0, sys.maxint )
            self.my_props.append( prop_id )
            self.d.request_property(prop, prop_id)

    def on_break(self, uri, line):
        self.store.clear()
        self.store.refresh()
        self.panel.set_property('sensitive', True)

    def restore_expanded(self):
        for r in self.expanded_rows:
            path = self.store.on_get_path( r )
            if path != None:
                self.panel.expand_row( path, False )

    def on_contexts(self, contexts):
        self.contexts = contexts
        for idx in range(len(contexts)):
            name, id = contexts[idx]
            self.store.data_arrive((name, None, 'context', name, 1))

        self.restore_expanded()

    def on_context(self, id, localid, props):
        if len( props ) > 0:
            self.store.data_arrive(( self.contexts[localid][0], props, 'context', self.contexts[localid][0], len(props) ))
        else:
            self.store.data_arrive(( self.contexts[localid][0], [('<Empty>', '','','<Empty>', 0)], 'context', self.contexts[localid][0], 1 ))
        self.restore_expanded()

    def append_row(self, tree, path, data):
        self.expanded_rows.append( self.store.on_get_iter( path ) )

    def on_busy(self):
        self.expanded_rows = []
        self.panel.map_expanded_rows( self.append_row, None )
        self.panel.set_property('sensitive', False)

    def on_stopped(self):
        self.store.clear()
        self.panel.set_property('sensitive', False)
