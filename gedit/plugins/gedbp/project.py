import gobject
import pickle

class ProjectException (Exception):
    pass

class Project:
    def __init__(self, disp):
        self.dir = ''
        self.raw = {}
        self.disp = disp
        self.filename = ''

    def load(self, filename):
        self.filename = filename
        try:
            f = open( self.filename, 'r' )
            self.raw = pickle.load( f )
        except:
            raise ProjectException, "Could not load project"
        print 'loaded',self.filename
        self.disp.project_loaded(self)

    def save(self, filename=None):
        print 'saving',filename,'|',self.filename
        if filename != None:
            self.filename = filename

        if self.filename == '':
            raise ProjectException, "No filename specified"

        self.disp.project_saving(self)
        f = open( self.filename, 'w' )
        pickle.dump( self.raw, f )

    def new(self):
        print 'new project'
        self.raw = {}
        self.filename = ''
        self.disp.project_created(self)

    def __setitem__(self, key, val):
        self.raw[key] = val

    def __getitem__(self, key):
        return self.raw[key]
