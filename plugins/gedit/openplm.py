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

import json
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
        self.username = ""

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
                _("Check out"), lambda a: self.checkout()),
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
            self.username = diag.get_username()
            self.password = diag.get_password()

            self.opener = urllib2.build_opener(urllib2.HTTPRedirectHandler(),
                                              urllib2.HTTPCookieProcessor())
            data = urllib.urlencode(dict(username=self.username,
                                         password=self.password, next="home/"))
            self.opener.open(self.SERVER + "login/", data)
        diag.destroy()

    def checkout(self):
        diag = CheckOutDialog(self._window, self)
        diag.run()
        diag.destroy()
    
    def get_data(self, url, data=None):
        if data:
            data_enc = urllib.urlencode(data)
            return json.load(self.opener.open(self.SERVER + url, data_enc)) 
        else:
            return json.load(self.opener.open(self.SERVER + url)) 


class CheckOutDialog(gtk.Dialog):
    
    def __init__(self, window, instance):
        super(CheckOutDialog, self).__init__(_("Login"), window,
                        gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,  
                        (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT))
        self.instance = instance
        docs = self.instance.get_data("api/docs/")
        table = gtk.Table(2, 3)
        self.vbox.pack_start(table)
        self.type_entry = gtk.combo_box_entry_new_text()
        for t in docs["types"]:
            self.type_entry.append_text(t)
        self.type_entry.child.set_text("Document")
        self.name_entry = gtk.Entry()
        self.rev_entry = gtk.Entry()
        self.fields = (("type", self.type_entry),
                  ("name", self.name_entry),
                  ("revision", self.rev_entry),
                 )
        for i, (text, entry) in enumerate(self.fields): 
            table.attach(gtk.Label(_(text.capitalize()+":")), 0, 1, i, i+1)
            table.attach(entry, 1, 2, i, i+1)
        
        search_button = gtk.Button(_("Search"))
        search_button.connect("clicked", self.search)
        self.vbox.pack_start(search_button)

        self.results_box = gtk.VBox()
        self.vbox.pack_start(self.results_box)
        self.vbox.show_all()

    def display_results(self, results):
        def expand_cb(widget):
            box = widget.get_child()
            if box.get_children():
                return
            files = self.instance.get_data("api/object/%s/files/" % widget.id)["files"]
            for f in files:
                hbox = gtk.HBox()
                label = gtk.Label(f["filename"])
                check_out = gtk.Button(_("Check out"), widget.id, f.id)
                hbox.pack_start(label)
                hbox.pack_start(check_out)
                box.pack_start(vox)
            widget.show_all()
        for child in self.results_box.get_children():
            child.destroy()
        for res in results:
            child = gtk.Expander("%(reference)s|%(type)s|%(revision)s" % res)
            child.id = res["id"]
            child.add(gtk.VBox())
            child.connect("activate", expand_cb)
            self.results_box.pack_start(child)
        self.results_box.show_all()
            
    def search(self, *args):
        data = {}
        for text, entry in self.fields:
            if hasattr(entry, "child"):
                entry = entry.child
            data[text] = entry.get_text()
        get = urllib.urlencode(data)
        self.display_results(self.instance.get_data("api/search/?%s" % get)["objects"])

    def check_out(self, button, doc, doc_file):
        self.instance.get_data("api/objects/%s/checkout/%s" % (doc, doc_file))
        

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


