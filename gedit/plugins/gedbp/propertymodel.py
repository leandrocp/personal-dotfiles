import gtk
from types import *

# ( '$a', '', '', '$a',  )

class PropertyModel (gtk.GenericTreeModel):
    '''
        values are stored as ( name, value, type, ref, child_count )
    '''
    def __init__(self, provider):
        gtk.GenericTreeModel.__init__( self )
        self.provider = provider

        self.values = {} #rowref -> value
        self.parents = {} #rowref -> rowref
        self.children = {} #rowref -> [rowref]
        self.changed = {} #rowref -> bool

    def clear(self):
        self.prev_values = self.values
        for i in range(len(self.values)):
            self.row_deleted((0,))
#        for ref in self.values:
#            self.row_deleted( self.on_get_path( ref ) )
        self.values = {}
        self.parents = {}
        self.children = {}

    def refresh(self):
        self.provider.request_property( None )

    def data_arrive(self, val): #val is [name, value, type(string), ref, child_count]
        print val
        name, value, ptype, ref, child_count = val

        self.values[ ref ] = val

        if self.parents.has_key( ref ):
            parent = self.parents[ ref ]
        else:
            parent = None

        wasloading = False

        if self.children.has_key(parent) and len(self.children[ parent ]) == 1 and (self.children[ parent ][0][:7] == 'loading'):
            wasloading = True
            self.children[parent] = []

        self.parents[ ref ] = parent

        update = True
        if self.children.has_key( parent ):
            try:
                print self.children[ parent ].index(ref)
            except ValueError:
                self.children[ parent ].append( ref )
                update = False
        else:
            self.children[ parent ] = [ref]
            update = False

        path = self.on_get_path( ref )
        i = self.get_iter( path )

        if wasloading or update:
            self.row_changed( path, i )
        else:
            self.row_inserted( path, i )

        if child_count > 0:
            self.row_has_child_toggled(path,i)

        if type( value ) == ListType:
            for k in value:
                n,v,t,r,c = k
                self.parents[ r ] = ref
                self.data_arrive( k )

    def remove(self, key):
        if not self.values.has_key(key):
            return

        if self.children.has_key(key):
            for child in self.children[key]:
                self.remove(child)

        parent = self.parents[key]

        path = self.on_get_path(key)
        self.children[parent].remove(key)
        del self.values[key]
        del self.parents[key]
        self.row_deleted( path )

    def on_get_flags(self):
        return gtk.TREE_MODEL_ITERS_PERSIST

    def on_get_n_columns(self):
        return 3 #name, value, type

    def on_get_column_type(self, index):
        return str

    def on_get_iter(self, path):
        print 'on_get_iter:',path
        ref = None
        for i in path:
            try:
                ref = self.children[ ref ][i]
            except KeyError:
                return None
        print ref
        return ref

    def on_get_path(self, rowref):
        print 'on_get_path:',rowref
        res = []
        finished = False
        while not finished:
            if not self.parents.has_key( rowref ):
                return None
            parent = self.parents[ rowref ]
            res.append( self.children[ parent ].index( rowref ) )
            rowref = parent
            finished = (rowref == None)
        res.reverse()
        return tuple(res)

    def on_get_value(self, rowref, column):
        if column == 0:
            print 'on_get_value',rowref
        if rowref[:7] == 'loading':
            if column == 0:
                return 'loading...'
            return 'black'

        if column == 0:
            return self.values[rowref][3] #ref

        if column == 4:
            if self.values.has_key( rowref ) and self.prev_values.has_key( rowref ):
                return {True: 'red', False: 'black'}\
                    [   (self.values[ rowref ] != self.prev_values[ rowref ]) and \
                        type(self.values[rowref]) != ListType and \
                        type(self.prev_values[rowref]) != ListType]
            else:
                return 'black'

        v = self.values[rowref][column]
        if type(v) == ListType:
            return ''
        else:
            return v

    def on_iter_next(self, rowref):
        print 'on_iter_next:',rowref
        if rowref[:7] == 'loading':
            return None

        parent = self.parents[ rowref ]
        i = self.children[ parent ].index( rowref )
        try:
            return self.children[ parent ][ i+1 ]
        except (IndexError, KeyError):
            print 'no next iter'
            return None

    def on_iter_children(self, parent):
        print 'on_iter_children:',parent
        name, value, ptype, ref, child_count = self.values[parent]

        if child_count == 0:
            return None

        if self.children.has_key( ref ):
            return self.children[ ref ][0]

        self.provider.request_property( ref )
        loading = 'loading' + parent
        self.parents[ loading ] = parent
        self.children[ parent ] = [loading]
        return loading

    def on_iter_has_child(self, rowref):
        print 'on_iter_has_child:',rowref
        if rowref[:7] == 'loading':
            return False
        name, value, ptype, ref, child_count = self.values[rowref]
        print child_count > 0
        return child_count > 0

    def on_iter_n_children(self, rowref):
        if rowref[:7] == 'loading':
            return 1
        name, value, ptype, ref, child_count = self.values[rowref]
        return child_count

    def on_iter_nth_child(self, parent, n):
        return self.children[ parent ][ n ]

    def on_iter_parent(self, child):
        return self.parents[ child ]
