# -*- coding: utf-8 -*-
#  OpenPLM plugin
#  
#  This plugin is based on Color Picker plugin by Jesse van den KieBoom
# 
#  Copyright (C) 2006 Jesse van den Kieboom,
#                2010 Pierre Cosquer
#   
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#   
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#   
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330,
#  Boston, MA 02111-1307, USA.

import urllib
import urllib2
import gedit, gtk
import gettext
from gpdefs import *

try:
    gettext.bindtextdomain(GETTEXT_PACKAGE, GP_LOCALEDIR)
    _ = lambda s: gettext.dgettext(GETTEXT_PACKAGE, s);
except:
    _ = lambda s: s

ui_str = """
<ui>
  <menubar name="MenuBar">
    <menu name="FileMenu" action="File">
      <placeholder name="open_plm">
        <menu name="OpenPLM" action="openplm">
            <menuitem name="login" action="login"/>
            <menuitem name="checkout" action="checkout"/>
         </menu>
      </placeholder>
    </menu>
  </menubar>
</ui>
"""

class OpenPLMPluginInstance(object):
    
    SERVER = "http://localhost:8000/"

    def __init__(self, plugin, window):
        self._window = window
        self._plugin = plugin
        self._activate_id = 0
        
        self.opener = None

        self.insert_menu()
        self.update()

        self._activate_id = self._window.connect('focus-in-event', \
                self.on_window_activate)

    def stop(self):
        self.remove_menu()

        if self._activate_id:
            self._window.handler_disconnect(self._activate_id)

        self._window = None
        self._plugin = None
        self._action_group = None
        self._activate_id = 0

    def insert_menu(self):
        manager = self._window.get_ui_manager()

        self._action_group = gtk.ActionGroup("GeditOpenPLMPluginActions")
        self._action_group.add_actions( 
                [("openplm", None, ("OpenPLM")),
                    ("login", None, _("Login"), None,
                _("Login"), lambda a: self.login()),
                 ("checkout", None, _("Check out"), None,
                _("Check out"), lambda a: self.login()),
                 ])

        manager.insert_action_group(self._action_group, -1)
        self._ui_id = manager.add_ui_from_string(ui_str)

    def remove_menu(self):
        manager = self._window.get_ui_manager()

        manager.remove_ui(self._ui_id)
        manager.remove_action_group(self._action_group)
        manager.ensure_update()

    def update(self):
        tab = self._window.get_active_tab()
        self._action_group.set_sensitive(tab != None)

        if not tab and self._plugin._dialog and \
                self._plugin._dialog.get_transient_for() == self._window:
            self._plugin._dialog.response(gtk.RESPONSE_CLOSE)

    def on_window_activate(self, window, event):
        self._plugin.dialog_transient_for(window)

    def login(self):
        diag = LoginDialog(self._window)
        resp = diag.run()
        if resp == gtk.RESPONSE_ACCEPT:
            username = diag.get_username()
            password = diag.get_password()
            auth_handler = urllib2.HTTPBasicAuthHandler()
            auth_handler.add_password(realm="", uri=self.SERVER ,
                                      user=username,
                                      passwd=password)

            self.opener = urllib2.build_opener(urllib2.HTTPRedirectHandler(),
                                              urllib2.HTTPCookieProcessor())
            data = urllib.urlencode(dict(username=username, password=password,
                                         next="home/"))
            f = self.opener.open(self.SERVER + "login/", data)

        diag.destroy()


class LoginDialog(gtk.Dialog):
    
    def __init__(self, window):
        super(LoginDialog, self).__init__(_("Login"), window,
                                         gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                                         (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                                          gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        table = gtk.Table(2, 2)
        self.vbox.pack_start(table)
        table.attach(gtk.Label(_("Username")), 0, 1, 0, 1)
        table.attach(gtk.Label(_("Password")), 0, 1, 1, 2)
        self.user_entry = gtk.Entry()
        table.attach(self.user_entry, 1, 2, 0, 1)
        self.pw_entry = gtk.Entry()
        self.pw_entry.set_visibility(False)
        table.attach(self.pw_entry, 1, 2, 1, 2)
        table.show_all()

    def get_username(self):
        return self.user_entry.get_text()

    def get_password(self):
        return self.pw_entry.get_text()


class OpenPLMPlugin(gedit.Plugin):
    DATA_TAG = "OpenPLMPluginInstance"

    def __init__(self):
        gedit.Plugin.__init__(self)
        self._dialog = None

    def get_instance(self, window):
        return window.get_data(self.DATA_TAG)

    def set_instance(self, window, instance):
        window.set_data(self.DATA_TAG, instance)

    def activate(self, window):
        self.set_instance(window, OpenPLMPluginInstance(self, window))

    def deactivate(self, window):
        self.get_instance(window).stop()
        self.set_instance(window, None)

    def update_ui(self, window):
        self.get_instance(window).update()

    def dialog_transient_for(self, window):
        if self._dialog:
            self._dialog.set_transient_for(window)


