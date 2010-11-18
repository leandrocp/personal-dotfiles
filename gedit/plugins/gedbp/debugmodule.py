import gedit

class DBGState:
    Idle = 0 #debugger is off
    Starting = 1
    Running = 2
    Tracing = 3
    Stopping = 4

class EventSubscriber:
    def on_break(self, uri, line):
        pass

    def on_busy(self):
        pass

    def on_stopped(self):
        pass

    def on_init(self, *params):
        pass

    def on_connect(self):
        pass

    def on_stopping(self):
        pass

    def on_evaluated(self, id, val):
        pass

    def on_contexts(self, contexts):
        pass

    def on_context(self, id, localid, context):
        pass

    def on_callstack(self, callstack):
        pass

    def on_property_got(self, prop, localid):
        pass

    def on_tab_loaded( self, taburi, tab ):
        pass

    def prepare_view(self, view):
        pass

    def project_created(self, project):
        pass

    def project_loaded(self, project):
        pass

    def project_saving(self, project):
        pass

    def on_breakpoint_mod(self, id, localid, state):
        pass

class DebugModule (EventSubscriber):
    pass
