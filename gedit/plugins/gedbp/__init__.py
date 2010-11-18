from gdbppy import GDBpPlugin
import os.path

gdbppy.PLUGINPATH = os.path.dirname( str(gdbppy).split()[3][1:-9] )+'/' # PATH extracted..
