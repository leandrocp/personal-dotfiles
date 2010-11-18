import xml.dom.minidom
import SocketServer
import socket
import sys
from base64 import b64encode, b64decode
import gobject
import random

def readToNULL( stream ):
    chunk = stream.recv( 1024, socket.MSG_PEEK )
    nullp = chunk.find( '\0' )
    res = stream.recv( nullp )
    stream.recv( 1 ) #null
    return res

class dbgp:

    def __init__(self, host, port, disp):
        self.host = host
        self.port = port
        self.uris = {}
        self.disp = disp

    def readNode(self, conn):
        respLen = int( readToNULL( conn ) )
        response = conn.recv( respLen )
        conn.recv( 1 ) #null
        return xml.dom.minidom.parseString( response )

    def parse_property( self, prop ):
        ptype = prop.getAttribute('type')

        if prop.hasAttribute('name'):
            name = prop.getAttribute('name')
        else:
            name = None

        if prop.hasAttribute('numchildren'):
            child_count = int(prop.getAttribute('numchildren'))
        else:
            child_count = 0

        if prop.hasAttribute('fullname'):
            ref = prop.getAttribute('fullname')
        else:
            ref = None

        isvalid = ptype != 'null'
        if isvalid:
            if prop.firstChild == None:
                return ( name, '', ptype, ref, child_count )

            if prop.hasChildNodes:
                value = prop.firstChild.nodeValue
            else:
                value = None

            if (ptype == 'string'):
                value = b64decode( prop.firstChild.nodeValue )

            if (ptype == 'array' or ptype == 'object'):
                value = []
                for child in prop.childNodes:
                    child = self.parse_property( child )
                    value.append( child )
            return ( name, value, ptype, ref, child_count )
        else:
            return ( name, None, ptype, ref, child_count )

    def onrecv(self, conn, *args):
        print 'onrecv'
        try:
            node = self.readNode( conn )
        except:
            return False

        print node.toprettyxml()

        doc = node.documentElement
        nodeType = doc.tagName

        if ( nodeType == 'init' ):
            accept = self.disp.on_init(
                doc.getAttribute('idekey'),
                doc.getAttribute('session'),
                doc.getAttribute('thread'),
                doc.getAttribute('parent'),
                doc.getAttribute('language'),
                doc.getAttribute('protocol_version'),
                doc.getAttribute('fileuri'),
                )
#            if not accept:
#                conn.close()

        if ( nodeType == 'response' ):
            cmd = doc.getAttribute( 'command' )

            error = None
            if doc.firstChild != None:
                if doc.firstChild.tagName == 'error':
                    error = str(doc.firstChild.firstChild.nodeValue)

            if ( cmd == 'stack_get' ):
                stack = []
                for entry in doc.childNodes:
                    stack.append( (entry.getAttribute('filename'), entry.getAttribute('lineno'), entry.getAttribute('where')) )
                self.disp.on_callstack(stack)

            elif ( cmd == 'eval' ):
                id = int(doc.getAttribute('transaction_id'))
                value = self.parse_property( doc.firstChild )
                self.disp.on_evaluated(id, value)

            elif ( cmd == 'source' ):
                i = int(doc.getAttribute('transaction_id'))
                uri = self.uris[i]
                source = b64decode( doc.firstChild.nodeValue )
                self.disp.on_source( uri, source )

            elif ( cmd == 'breakpoint_set' ):
                self.disp.on_breakpoint_mod( int(doc.getAttribute('id')), int(doc.getAttribute('transaction_id')), doc.getAttribute( 'state' ) );

            elif ( cmd == 'context_names' ):
                res = []
                for context in doc.childNodes:
                    res.append(( context.getAttribute('name'), int(context.getAttribute('id')) ))
                self.disp.on_contexts(res)

            elif ( cmd == 'context_get' ):
                res = []
                for prop in doc.childNodes:
                    res.append( self.parse_property( prop ) )
                id = int(doc.getAttribute('context'))
                localid = int(doc.getAttribute('transaction_id'))
                self.disp.on_context( id, localid, res )

            elif ( cmd == 'property_get' ):
                if error != None:
                    self.disp.on_property_got( error, int( doc.getAttribute('transaction_id') ) )

                res = self.parse_property( doc.firstChild )
                self.disp.on_property_got( res, int( doc.getAttribute('transaction_id') ) )

            elif ( cmd == 'run' or cmd == 'step_into' or cmd == 'step_over' or cmd == 'step_out' or cmd == 'stop' ):
                status = doc.getAttribute('status')
                if ( status == 'break' ):
                    print '============================================ BREAK'
                    self.disp.on_break(
                        doc.firstChild.getAttribute( 'filename' ),
                        int( doc.firstChild.getAttribute( 'lineno' ) )
                     )

                if ( status == 'stopping' ):
                    self.disp.on_stopping()

                if ( status == 'stopped' ):
                    self.disp.on_stopped()
                    return False #no more business

        return True

    def listener(self, sock, *args):
        conn, addr = self.ss.accept()
        self.client = conn
        self.disp.on_connect()
        gobject.io_add_watch( conn, gobject.IO_IN, self.onrecv )
        return True

    def start(self):
        self.ss = socket.socket()
        self.ss.bind((self.host, self.port))
        self.ss.listen(1)
        print 'Listening...'
        gobject.io_add_watch( self.ss, gobject.IO_IN, self.listener )

    def stop(self):
        self.ss.close()

    def send_command(self, command):
        print command
        self.client.send( command )

    def set_breakpoint(self, uri, line, localid ):
        self.send_command( "breakpoint_set -t line -f %s -n %s -i %d\0" % (uri, line, localid) )

    def remove_breakpoint( self, id ):
        self.send_command( "breakpoint_remove -d %d -i 1\0" % id )

    def modify_breakpoint( self, id, uri, line ):
        self.send_command( "breakpoint_update -d %d -f %s -n %s -i 1\0" % (id, uri, line) )

    def run(self):
        self.send_command( "run -i 1\0" )
        self.disp.on_busy()

    def stop(self):
        self.send_command( "stop -i 1\0" )

    def step_into(self):
        self.send_command( "step_into -i 1\0" )
        self.disp.on_busy()

    def step_over(self):
        self.send_command( "step_over -i 1\0" )
        self.disp.on_busy()

    def step_out(self):
        self.send_command( "step_out -i 1\0" )
        self.disp.on_busy()

    def request_callstack(self):
        self.send_command( "stack_get -i 1\0" )

    def request_eval(self, id, expr):
        self.send_command( "eval -i %d -- %s\0" % (id, b64encode( expr ) ) )

    def request_source( self, uri ):
        i = random.randint( 0, sys.maxint )
        self.uris[ i ] = uri
        self.send_command( "source -f %s -i %d\0" % (uri, i) )

    def request_contexts(self):
        self.send_command( "context_names -i 1\0" )

    def request_context(self, id, localid):
        self.send_command( "context_get -d 0 -c %d -i %d\0" % (id, localid) )

    def request_property(self, name, localid):
        self.send_command( "property_get -n %s -d 0 -i %d\0" % (name, localid) )

if __name__ == '__main__':
    start()
