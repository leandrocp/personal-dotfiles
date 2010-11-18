import gtk
import gobject

class SimpleTableIterator:
    def __init__( self, table ):
        self.table = table
        self.i = 0

    def next(self):
        if ( self.i == self.table.length() ):
            raise StopIteration

        res = self.table[ self.i ]
        self.i = self.i + 1
        return res

class SimpleTable(gtk.TreeView):

    NEW_ITEM_TITLE = '<type here to add new item>'

    def __init__(self, types, titles, appendable = False):
        self.store = gtk.ListStore( *types )
        gtk.TreeView.__init__( self, self.store )

        self.empty_row_items = []

        idx = 0
        for title in titles:
            column = gtk.TreeViewColumn( title )
            column.set_resizable( True )
            column.set_expand( True )
            self.append_column( column )
            rend = gtk.CellRendererText()
            if ( appendable and (idx == 0) ):
                rend.set_property( 'editable', True )
                rend.connect( 'edited', self.cell_edited_signal )

            column.pack_start( rend )
            print idx
            column.add_attribute( rend, 'text', idx )
            self.empty_row_items.append( '' )
            idx = idx + 1

        self.columns = idx
        self.appendable = appendable

        self.empty_row_items[0] = SimpleTable.NEW_ITEM_TITLE
        print self.empty_row_items
        if ( appendable ):
            self.store.append( self.empty_row_items )

        self.connect( 'key-press-event', self.onkeypress )

    def remove_selected( self, model, path, i ):
        if ( (model.get_value( i, 0 ) != SimpleTable.NEW_ITEM_TITLE) or not self.appendable ):
            model.remove(i)

    def onkeypress(self, widget, event):
        if not self.appendable:
            return False
        if ( event.keyval == gtk.keysyms.Delete ):
            sel = self.get_selection()
            sel.selected_foreach( self.remove_selected )
            self.emit('deleted')
            return True
        return False

    def cell_edited_signal( self, renderer, path, new_text ):
        idx = int(path[0])
        self.store.set_value( self.store.iter_nth_child(None, idx), 0, new_text )

        if ( self.store.iter_n_children( None ) == idx+1 ):
            self.store.append( self.empty_row_items )
            self.emit( 'appended', idx )
        self.emit( 'edited', idx )

    def remove( self, idx ):
        i = self.store.iter_nth_child( None, idx )
        self.store.remove(i)

    def append( self, values ):
        print values
        if self.appendable:
            self.remove( self.store.iter_n_children( None )-1 )
        self.store.append( values )
        if self.appendable:
            self.store.append( self.empty_row_items )
            self.emit( 'edited', self.length()-1 )

    def length(self):
        if self.appendable:
            return self.store.iter_n_children( None )-1
        else:
            return self.store.iter_n_children( None )

    def __iter__(self):
        return SimpleTableIterator( self )

    def __getitem__(self, idx):
        print idx
        i = self.store.iter_nth_child( None, idx )
        if i == None:
            return None
        res = []
        for row in range( 0, self.store.get_n_columns() ):
            res.append( self.store.get_value( i, row ) )
        return tuple(res)

    def __setitem__(self, idx, val):
        i = self.store.iter_nth_child( None, idx )
        if i == None:
            return None

        for row in range( 0, self.store.get_n_columns() ):
            self.store.set_value( i, row, val[row] )

    def find(self, *val):
        idx = 0
        for v in self:
            print v,' vs ',val
            if v == val:
                print 'match!'
                return idx
            idx = idx + 1
        return None

    def clear(self):
        self.store.clear()

gobject.type_register( SimpleTable )
gobject.signal_new( 'appended', SimpleTable, gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (int,) )
gobject.signal_new( 'edited', SimpleTable, gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (int,) )
gobject.signal_new( 'deleted', SimpleTable, gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, () )
