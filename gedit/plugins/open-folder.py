# -*- coding: utf-8 -*-
#
# Simple Gedit plugin that uses nautilus to open the folder containing 
# the current file.
#
# Copyright © 2008, Kevin McGuinness <kevin.mcguinness@gmail.com>
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 51
# Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#

import os 
import os.path
import gedit
import gtk
import gconf


# UI Manager XML
OPEN_FOLDER_UI = """
<ui>
  <menubar name="MenuBar">
    <menu name="ToolsMenu" action="Tools">
      <placeholder name="ToolsOps_2">
        <menuitem name="Open Folder" action="OpenFolder"/>
      </placeholder>
    </menu>
  </menubar>
  
  <popup name="NotebookPopup" action="NotebookPopupAction">
    <placeholder name="NotebookPupupOps_1">
      <menuitem name="Open Folder" action="OpenFolder"/>
    </placeholder>
  </popup>
</ui>
"""


# Main plugin class
class OpenFolderPlugin(gedit.Plugin):
    """ Plugin to allow opening the folder containing the active document."""

    def __init__(self):
        gedit.Plugin.__init__(self)


    def on_open_folder(self, action, window):
        """Open the containing folder with nautilus."""
        
        active_doc = window.get_active_document()
        doc_uri = active_doc.get_uri() if active_doc else None
 
        if not doc_uri: 
            return

        folder_url = os.path.dirname(doc_uri)
        
        # spawn process (we can wait: nautilus will return)
        program = 'nautilus'
        code = os.spawnlpe(os.P_WAIT, program, program, folder_url, os.environ)
        if code != 0:
            message = 'Error opening the folder:\n<b>%s</b>.\n\n' \
                '(%s exited with code <b>%d</b>)' \
                 % (program, folder_url, code)
            self.error_message(window, message)


    def error_message(self, window, message):
        """Display error message."""

        dialog = gtk.MessageDialog(
            parent         = window,
            flags          = gtk.DIALOG_DESTROY_WITH_PARENT,
            type           = gtk.MESSAGE_ERROR,
            buttons        = gtk.BUTTONS_OK
        )
        dialog.set_markup(message)
        dialog.set_title('Error')
        dialog.connect('response', lambda dialog, response: dialog.destroy())
        dialog.show()


    def activate(self, window):
        """Activate plugin."""  
        
        action = (
            'OpenFolder', # name 
            'gtk-directory', # icon stock id
            'Open _Folder', # label
            '<Shift><Ctrl>F',# accelerator
            'Open the folder containing the current document', # tooltip
            self.on_open_folder # callback
        )
        
        action_group = gtk.ActionGroup(self.__class__.__name__)
        action_group.add_actions([action], window)

        ui_manager = window.get_ui_manager()
        ui_manager.insert_action_group(action_group, 0)
        ui_id = ui_manager.add_ui_from_string(OPEN_FOLDER_UI)
        
        data = { 'action_group': action_group, 'ui_id': ui_id }
        window.set_data(self.__class__.__name__, data)
        self.update_ui(window)


    def deactivate(self, window):
        """Deactivate plugin."""

        data = window.get_data(self.__class__.__name__)
        ui_manager = window.get_ui_manager()
        ui_manager.remove_ui(data['ui_id'])
        ui_manager.remove_action_group(data['action_group'])
        ui_manager.ensure_update()
        window.set_data(self.__class__.__name__, None)


    def update_ui(self, window):
        """Update the sensitivities of actions."""

        windowdata = window.get_data(self.__class__.__name__)
        doc = window.get_active_document()
        sensitive = bool(doc and doc.get_uri())
        windowdata['action_group'].set_sensitive(sensitive)


