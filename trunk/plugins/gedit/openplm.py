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

import os
import shutil
import json
import urllib

# sudo easy_install poster
from poster.encode import multipart_encode
from poster.streaminghttp import StreamingHTTPRedirectHandler, StreamingHTTPHandler

import urllib2
import gedit, gtk
import gettext
import gpdefs

try:
    gettext.bindtextdomain(gpdefs.GETTEXT_PACKAGE, gpdefs.GP_LOCALEDIR)
    _ = lambda s: gettext.dgettext(gpdefs.GETTEXT_PACKAGE, s);
except:
    _ = lambda s: s

ui_str = """
<ui>
  <menubar name="MenuBar">
    <menu name="FileMenu" action="File">
      <placeholder name="open_plm" position="top">
        <menu name="OpenPLM" action="openplm">
            <menuitem name="login" action="login"/>
            <menuitem name="checkout" action="checkout"/>
            <menuitem name="checkin" action="checkin"/>
         </menu>
         <separator/>
      </placeholder>
    </menu>
  </menubar>
</ui>
"""

class OpenPLMPluginInstance(object):
    
    SERVER = "http://localhost:8000/"
    OPENPLM_DIR = os.path.expanduser("~/.openplm")
    PLUGIN_DIR = os.path.join(OPENPLM_DIR, "gedit")
    CONF_FILE = os.path.join(PLUGIN_DIR, "conf.json")

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

        try:
            os.makedirs(self.OPENPLM_DIR, 0700)
        except os.error:
            pass

    def stop(self):
        self.remove_menu()

        if self._activate_id:
            self._window.handler_disconnect(self._activate_id)

        self._window = None
        self._plugin = None
        self._action_group1 = None
        self._action_group2 = None
        self._activate_id = 0

    def insert_menu(self):
        manager = self._window.get_ui_manager()

        self._action_group1 = gtk.ActionGroup("GeditOpenPLMPluginActions1")
        self._action_group1.add_actions( 
                [("openplm", None, ("OpenPLM")),
                 ("login", None, _("Login"), None,
                    _("Login"), lambda a: self.login()),
                 ])

        manager.insert_action_group(self._action_group1, -1)
        self._action_group2 = gtk.ActionGroup("GeditOpenPLMPluginActions2")
        self._action_group2.add_actions([ 
                 ("checkout", None, _("Check-out"), None,
                     _("Check out"), lambda a: self.check_out_cb()),
                 ("checkin", None, _("Check-in"), None,
                     _("Check-in"), lambda a: self.check_in_cb()),
                 ])
        self._action_group2.set_sensitive(False)
        manager.insert_action_group(self._action_group2, -1)
        self._ui_id = manager.add_ui_from_string(ui_str)

    def remove_menu(self):
        manager = self._window.get_ui_manager()

        manager.remove_ui(self._ui_id)
        manager.remove_action_group(self._action_group1)
        manager.remove_action_group(self._action_group2)
        manager.ensure_update()

    def update(self):
        pass

    def on_window_activate(self, window, event):
        self._plugin.dialog_transient_for(window)

    def login(self):
        diag = LoginDialog(self._window)
        resp = diag.run()
        if resp == gtk.RESPONSE_ACCEPT:
            self.username = diag.get_username()
            self.password = diag.get_password()

            self.opener = urllib2.build_opener(StreamingHTTPHandler(),
                                               StreamingHTTPRedirectHandler(),
                                              urllib2.HTTPCookieProcessor())
            data = urllib.urlencode(dict(username=self.username,
                                         password=self.password, next="home/"))
            self.opener.open(self.SERVER + "login/", data)
            self._action_group2.set_sensitive(True)
            self.load_managed_files()
        diag.destroy()

    def check_out_cb(self):
        diag = CheckOutDialog(self._window, self)
        diag.run()
        diag.destroy()
    
    def get_data(self, url, data=None):
        if data:
            data_enc = urllib.urlencode(data)
            return json.load(self.opener.open(self.SERVER + url, data_enc)) 
        else:
            return json.load(self.opener.open(self.SERVER + url)) 

    def check_out(self, doc, doc_file):
        self.document = doc
        self.get_data("api/object/%s/checkout/%s/" % (doc["id"], doc_file["id"]))
        f = self.opener.open(self.SERVER + "file/%s/" % doc_file["id"])
        rep = os.path.join(self.PLUGIN_DIR, doc["type"], doc["reference"],
                           doc["revision"])
        try:
            os.makedirs(rep, 0700)
        except os.error:
            # directory already exists
            pass
        dst_name = os.path.join(rep, doc_file["filename"])
        dst = open(dst_name, "wb")
        shutil.copyfileobj(f, dst)
        f.close()
        dst.close()
        self.add_managed_file(doc, doc_file, dst_name)
        gedit.commands.load_uri(self._window, "file://" + dst_name, None, -1)
        gdoc = self._window.get_active_document()
        gdoc.set_data("openplm_doc", doc)
        gdoc.set_data("openplm_file", doc_file)
        gdoc.set_data("openplm_path", dst_name)

    def add_managed_file(self, document, doc_file, path):
        f = open(self.CONF_FILE, "r")
        try:
            data = json.load(f)
        except ValueError:
            data = {}
        f.close()
        documents = data.get("documents", {})
        doc = documents.get(document["id"], dict(document))
        files = doc.get("files", {})
        files[doc_file["id"]] = path
        doc["files"] = files
        documents["id"] = doc
        data["documents"] = documents
        f = open(self.CONF_FILE, "w")
        json.dump(data, f)
        f.close()

    def get_managed_files(self):
        with open(self.CONF_FILE, "r") as f:
            try:
                data = json.load(f)
            except ValueError:
                data = {}
            files = []
            for doc in data.get("documents", {}).itervalues():
                files.extend((d, doc) for d in doc.get("files", {}).items())
            return files
    
    def load_managed_files(self):
        for (doc_file_id, path), doc in self.get_managed_files():
            gedit.commands.load_uri(self._window, "file://" + path, None, -1)
            gdoc = self._window.get_active_document()
            gdoc.set_data("openplm_doc", doc)
            gdoc.set_data("openplm_file_id", doc_file_id)
            gdoc.set_data("openplm_path", path)

    def check_in(self, unlock):
        gdoc = self._window.get_active_document()
        doc = gdoc.get_data("openplm_doc")
        doc_file_id = gdoc.get_data("openplm_file_id")
        path = gdoc.get_data("openplm_path")
        if doc and doc_file_id and path:
            gedit.commands.save_document(self._window, gdoc)
            # headers contains the necessary Content-Type and Content-Length
            # datagen is a generator object that yields the encoded parameters
            datagen, headers = multipart_encode({"filename": open(path, "rb")})
            # Create the Request object
            url = self.SERVER + "api/object/%s/checkin/%s/" % (doc["id"], doc_file_id)
            request = urllib2.Request(url, datagen, headers)
            res = self.opener.open(request)
            if not unlock:
                self.get_data("api/object/%s/lock/%s/" % (doc["id"], doc_file_id))
        else:
            # TODO
            print 'can not check in'
            pass

    def check_in_cb(self):
        gdoc = self._window.get_active_document()
        doc = gdoc.get_data("openplm_doc")
        name = os.path.basename(gdoc.get_data("openplm_path"))
        diag = CheckInDialog(self._window, self, doc, name)
        resp = diag.run()
        if resp == gtk.RESPONSE_ACCEPT:
            self.check_in(diag.get_unlocked())
        diag.destroy()


class CheckInDialog(gtk.Dialog):
    
    def __init__(self, window, instance, doc, filename):
        super(CheckInDialog, self).__init__(_("Check-in"), window,
                        gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,  
                        (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                        "Check-in", gtk.RESPONSE_ACCEPT))
        self.instance = instance
        label = gtk.Label("%s|%s|%s"% (doc["reference"], doc["revision"],
                                       doc["type"]))
        self.vbox.pack_start(label)
        label2 = gtk.Label(filename)
        self.vbox.pack_start(label2)
        self.unlock_button = gtk.CheckButton("Unlock ?")
        self.vbox.pack_start(self.unlock_button)
        self.vbox.show_all()

    def get_unlocked(self):
        return self.unlock_button.get_active()
        

class CheckOutDialog(gtk.Dialog):
    
    def __init__(self, window, instance):
        super(CheckOutDialog, self).__init__(_("Check-out"), window,
                        gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,  
                        (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT))
        self.instance = instance
        docs = self.instance.get_data("api/docs/")
        self.types = docs["types"]
        table = gtk.Table(2, 3)
        self.vbox.pack_start(table)
        self.type_entry = gtk.combo_box_entry_new_text()
        for t in docs["types"]:
            self.type_entry.append_text(t)
        self.type_entry.child.set_text("Document")
        self.type_entry.connect("changed", self.type_entry_activate_cb)
        self.name_entry = gtk.Entry()
        self.rev_entry = gtk.Entry()
        self.fields = [("type", self.type_entry),
                       ("reference", self.name_entry),
                       ("revision", self.rev_entry),
                      ]
        for i, (text, entry) in enumerate(self.fields): 
            table.attach(gtk.Label(_(text.capitalize()+":")), 0, 1, i, i+1)
            table.attach(entry, 1, 2, i, i+1)
        
        self.advanced_table = gtk.Table(2, 3)
        self.advanced_fields = []
        self.vbox.pack_start(self.advanced_table)
        self.display_fields("Document")
        
        search_button = gtk.Button(_("Search"))
        search_button.connect("clicked", self.search)
        self.vbox.pack_start(search_button)

        self.results_box = gtk.VBox()
        self.vbox.pack_start(self.results_box)
        self.vbox.show_all()

    def type_entry_activate_cb(self, entry):
        typename = entry.child.get_text()
        if typename in self.types:
            self.display_fields(typename)

    def display_fields(self, typename):
        fields = self.instance.get_data("api/search_fields/%s/" % typename)["fields"]
        temp = {}
        for field, entry in self.advanced_fields:
            temp[field] = self.get_value(entry)
        for child in self.advanced_table.get_children():
            child.destroy()
        self.advanced_fields = []
        self.advanced_table.resize(2, len(fields))
        for i, (text, choices) in enumerate(fields):
            self.advanced_table.attach(gtk.Label(_(text.capitalize()+":")),
                                       0, 1, i, i+1)
            if choices:
                model = gtk.ListStore(object, str)
                if [u'', u'---------'] not in choices:
                    choices = ([u'', u'---------'],) + tuple(choices)
                for c in choices:
                    model.append(c)
                widget = gtk.ComboBox(model)
                cell = gtk.CellRendererText()
                widget.pack_start(cell, True)
                widget.add_attribute(cell, 'text', 1)  
            else:
                widget = gtk.Entry()
            if text in temp:
                self.set_value(widget, temp[text])
            self.advanced_table.attach(widget, 1, 2, i, i+1)
            self.advanced_fields.append((text, widget))
        self.advanced_table.show_all()

    def get_value(self, entry):
        if isinstance(entry, gtk.ComboBoxEntry):
            value = entry.child.get_text()
        elif isinstance(entry, gtk.ComboBox):
            model = entry.get_model()
            active = entry.get_active()
            if active < 0:
                value = ""
            else:
                value = model[active][0]
        elif isinstance(entry, gtk.Entry):
            value = entry.get_text()
        return value

    def set_value(self, entry, value):
        if isinstance(entry, gtk.ComboBoxEntry):
            entry.child.set_text(entry)
        elif isinstance(entry, gtk.ComboBox):
            model = entry.get_model()
            for i, it in enumerate(iter(model)):
                if value == it[0]:
                    entry.set_active(i)
                    return
        elif isinstance(entry, gtk.Entry):
            entry.set_text(value)


    def display_results(self, results):
        def expand_cb(widget):
            box = widget.get_child()
            if box.get_children():
                return
            files = self.instance.get_data("api/object/%s/files/" % widget.res["id"])["files"]
            for f in files:
                hbox = gtk.HBox()
                label = gtk.Label(f["filename"])
                check_out = gtk.Button(_("Check out"))
                check_out.connect("clicked", self.check_out, widget.res, f)
                hbox.pack_start(label)
                hbox.pack_start(check_out)
                box.pack_start(hbox)
            widget.show_all()
        for child in self.results_box.get_children():
            child.destroy()
        for res in results:
            child = gtk.Expander("%(reference)s|%(type)s|%(revision)s" % res)
            child.res = res
            child.add(gtk.VBox())
            child.connect("activate", expand_cb)
            self.results_box.pack_start(child)
        self.results_box.show_all()
            
    def search(self, *args):
        data = {}
        for text, entry in self.fields + self.advanced_fields:
            value = self.get_value(entry)
            if value:
                data[text] = value
        get = urllib.urlencode(data)
        self.display_results(self.instance.get_data("api/search/?%s" % get)["objects"])

    def set_doc(self, doc):
        self.document = doc

    def check_out(self, button, doc, doc_file):
        self.instance.check_out(doc, doc_file)
        self.destroy()
        

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
        self.user_entry.connect("activate", self.user_entry_activate_cb)
        table.attach(self.user_entry, 1, 2, 0, 1)
        self.pw_entry = gtk.Entry()
        self.pw_entry.set_visibility(False)
        self.pw_entry.connect("activate", self.pw_entry_activate_cb)
        table.attach(self.pw_entry, 1, 2, 1, 2)
        table.show_all()
    
    def user_entry_activate_cb(self, entry):
        self.do_move_focus(self, gtk.DIR_TAB_FORWARD)

    def pw_entry_activate_cb(self, entry):
        self.response(gtk.RESPONSE_ACCEPT)

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


