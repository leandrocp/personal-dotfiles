#!/bin/sh
# Kill all runing instances if exists
# killall gedit

gedit_dir="$HOME/.gnome2/gedit"

# Copy gedit-improved executable
#-------------------------------------------------------------------------------
sudo mkdir -p /usr/share/gedit-2/gedit-improved
sudo cp -f "$gedit_dir/gim.py" /usr/share/gedit-2/gedit-improved/gim.py
sudo ln -nfs /usr/share/gedit-2/gedit-improved/gim.py /usr/bin/gim
sudo ln -nfs /usr/share/gedit-2/gedit-improved/gim.py /usr/bin/e
sudo ln -nfs /usr/share/gedit-2/gedit-improved/gim.py /usr/bin/g

# Register mime types
#-------------------------------------------------------------------------------
sudo cp -f $gedit_dir/mime/*.xml /usr/share/mime/packages/
sudo update-mime-database /usr/share/mime

# Copy language definitions
#-------------------------------------------------------------------------------
sudo cp -f $gedit_dir/lang-specs/*.lang /usr/share/gtksourceview-2.0/language-specs/

# Copy Tags
#-------------------------------------------------------------------------------
if [ ! -d /usr/share/gedit-2/plugins/taglist/ ]
then
  sudo mkdir -p /usr/share/gedit-2/plugins/taglist/
fi
sudo cp -f $gedit_dir/tags/*.tags.gz /usr/share/gedit-2/plugins/taglist/

# We may have to install some packages
#-------------------------------------------------------------------------------
sudo apt-get install gedit-plugins python-webkit python-mysqldb libgtksourceview2.0-0

# Default config
#-------------------------------------------------------------------------------
echo -n "Do you want to activate default plugin and configuration set? [y,N]:"
read answer
case "$answer" in
    [yY])
        `gconftool-2 --set /apps/gedit-2/plugins/active-plugins -t list --list-type=str [gedbp,externaltools,open-folder,gsqlclient,regex_replace,FindInFiles,controlyourtabs,zencoding,smart_indent,text_tools,completion,quickhighlightmode,gemini,trailsave,snapopen,filebrowser,snippets,modelines,smartspaces,docinfo,terminal,codecomment,colorpicker,indent]`
        `gconftool-2 --set /apps/gedit-2/preferences/editor/auto_indent/auto_indent -t bool true`
        `gconftool-2 --set /apps/gedit-2/preferences/editor/bracket_matching/bracket_matching -t bool true`
        `gconftool-2 --set /apps/gedit-2/preferences/editor/current_line/highlight_current_line -t bool true`
        `gconftool-2 --set /apps/gedit-2/preferences/editor/cursor_position/restore_cursor_position -t bool true`
        `gconftool-2 --set /apps/gedit-2/preferences/editor/line_numbers/display_line_numbers -t bool true`
        `gconftool-2 --set /apps/gedit-2/preferences/editor/right_margin/display_right_margin -t bool true`
        `gconftool-2 --set /apps/gedit-2/preferences/editor/right_margin/right_margin_position -t int 80`
        `gconftool-2 --set /apps/gedit-2/preferences/editor/colors/scheme -t str railscastsimp`
        `gconftool-2 --set /apps/gedit-2/preferences/editor/tabs/insert_spaces -t bool true`
        `gconftool-2 --set /apps/gedit-2/preferences/editor/tabs/tabs_size -t int 2`
        `gconftool-2 --set /apps/gedit-2/preferences/editor/wrap_mode/wrap_mode -t str GTK_WRAP_NONE`
        `gconftool-2 --set /apps/gedit-2/preferences/editor/save/create_backup_copy -t bool false`
        echo "Configuration set."
        ;;
        *)
        echo "No config performed."
        ;;
esac

