import gedit
import tempfile
from debugmodule import *

class Tabs (EventSubscriber):
    def __init__(self, window, plugin, disp):
        self.window = window
        self.plugin = plugin
        self.disp = disp
        disp.add_subscriber( self )
        window.connect( "tab-added", self.tab_added_signal )

    def project_loaded(self, project):
        for tab in project['tabs']:
            print 'opening',tab
            self.open_tab( tab, 0 )

    def project_created(self, project):
        project['tabs'] = [] #tab uris

    def project_saving(self, project):
        for view in self.window.get_views():
            self.plugin.project['tabs'].append( view.get_buffer().get_uri() )

    def tab_added_signal(self, window, tab):
        doc = tab.get_document()
        print 'tab_added',doc.get_uri()
        doc.connect( 'loaded', self.doc_loaded_signal )
        return True

    def open_tab( self, uri, line ):
        tab = self.window.get_tab_from_uri( uri )
        if tab == None:
            tab = self.window.create_tab_from_uri( uri, gedit.encoding_get_utf8(), line, False, True )
            if ( tab == None ):
                return None

        self.window.set_active_tab(tab)
        if line != None:
            doc = tab.get_document()
            doc.goto_line( line - 1 )
            i = doc.get_iter_at_line( line - 1 )
            tab.get_view().scroll_to_iter( i, 0.1 )
        return tab

    def create_remote_tab(self, uri, contents):
        return None

    def get_tab( self, uri ):
        return self.window.get_tab_from_uri( uri )

    def doc_loaded_signal(self, doc, data):
        uri = doc.get_uri()
        tab = self.window.get_tab_from_uri( uri )
        self.disp.on_tab_loaded( uri, tab )
