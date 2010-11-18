import gtk
import gedit
from simpletable import SimpleTable
from types import *
import sys
import random
from propertymodel import PropertyModel
from debugmodule import *

class Watches (DebugModule):
    def __init__( self, window, plugin, debugger ):
        self.window = window
        self.plugin = plugin
        self.d = debugger
        self.icon = gtk.gdk.pixbuf_new_from_file( DebugModule.PLUGINPATH+'watch.png' )

        self.store = PropertyModel( self )
        self.stub_store = gtk.ListStore(str,str,str,str,str)
        self.panel = gtk.TreeView()
        self.panel.set_model( self.stub_store )
        self.store.view = self.panel

        rend = gtk.CellRendererText()
#        rend.set_property( 'editable', True )
#        rend.connect( 'edited', self.cell_edited )

        col = gtk.TreeViewColumn( 'Item', rend, text=0, foreground=4 )
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
        scrollbox.show()

        add = gtk.HBox()
        self.addentry = gtk.Entry()
        addbtn = gtk.Button('Add')

        addbtn.connect('clicked', self.add_clicked_signal)
        self.panel.connect('key-press-event', self.key_pressed_signal)

        add.pack_start( self.addentry )
        self.addentry.show()
        add.pack_start( addbtn, False )
        addbtn.show()
        add.show()

        box = gtk.VBox()
        box.pack_start( scrollbox )
        box.pack_start( add, False )

        img = gtk.Image()
        img.set_from_pixbuf( self.icon )
        window.get_side_panel().add_item( box, 'Watches', img )

        self.watches = []
        self.refreshing = False

        self.my_props = {} #id -> property name
        self.expanded_rows = []

    def request_property(self, prop):
        print 'requesting',prop,'for watches...'
        print self.watches
        if prop == None:
            for watch in self.watches:
                prop_id = random.randint( 0, sys.maxint )
                self.my_props[ prop_id ] = watch
                self.d.request_property( watch, prop_id )
        else:
            prop_id = random.randint( 0, sys.maxint )
            self.my_props[ prop_id ] = prop
            self.d.request_property(prop, prop_id)

    def add_clicked_signal(self, param):
        v = self.addentry.get_text()
        self.add_watch( v )
        self.addentry.set_text('')

    def key_pressed_signal(self, treeview, evt):
        if evt.keyval == gtk.keysyms.Delete:
            model, i = self.panel.get_selection().get_selected()
            watch = model.get(i,0)[0]
            print 'Removing',watch
            idx = self.watches.index(watch)
            self.watches.remove(watch)

            stub_iter = self.stub_store.iter_nth_child(None, idx)
            self.stub_store.remove(stub_iter)

            self.store.remove(watch)

    def add_watch(self, v):
        print v
        self.stub_store.append((v,'','','','black'))
        self.watches.append(v)
        if self.plugin.state == DBGState.Tracing:
            self.request_property(v)

    def clear_watches(self):
        self.stub_store.clear()
        self.watches = []

    def menu_item_signal(self, item):
        doc = item.get_data('view').get_buffer()
        sel = doc.get_selection_bounds()
        w = doc.get_text( *sel )
        self.add_watch( w )

    def context_menu_signal(self, view, menu):
        item = gtk.ImageMenuItem( "Add Watch" )

        img = gtk.Image()
        img.set_from_pixbuf( self.icon )
        item.set_image( img )

        item.connect( 'activate', self.menu_item_signal )
        item.show()
        item.set_data('view', view)
        item.set_sensitive( view.get_buffer().get_has_selection() )
        menu.insert( item, 0 )
        return True

    def prepare_view(self, view):
        print 'preparing view',view
        view.connect( "populate-popup", self.context_menu_signal )

    def on_property_got(self, prop, localid):
        try:
            print localid,self.my_props
            prop_name = self.my_props[ localid ]
        except:
            return
        del self.my_props[ localid ]

        if type( prop ) == StringType:
            self.store.data_arrive(( prop_name, prop, '<error>', prop_name, 0 ))
        else:
            self.store.data_arrive( prop )

        if len(self.my_props) == 0:
            for r in self.expanded_rows:
                print 'expanding',r
                path = self.store.on_get_path( r )
                if path != None:
                    self.panel.expand_row( path, False )

    def append_row(self, tree, path, data):
        self.expanded_rows.append( self.store.on_get_iter( path ) )

    def on_break(self, uri, line):
        self.panel.set_model( self.store )
        self.store.clear()
        self.store.refresh()

    def on_busy(self):
        self.expanded_rows = []
        self.panel.map_expanded_rows( self.append_row, None )
        print self.expanded_rows

        self.panel.set_model( self.stub_store )

    def on_stopped(self):
        self.panel.set_model( self.stub_store )

    def project_saving(self, project):
        project['watches'] = self.watches

    def project_loaded(self, project):
        self.clear_watches()
        for w in project['watches']:
            self.add_watch(w)

    def project_created(self, project):
        self.clear_watches()
        project['watches'] = []
