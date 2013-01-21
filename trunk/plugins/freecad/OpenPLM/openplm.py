# OpenPLM module
# (c) 2013 LinObject SAS
#

#***************************************************************************
#*   (c) LinObject SAS (contact@linobject.com) 2013                        *
#*                                                                         *
#*   This file is part of the OpenPLM plugin for FreeCAD.                  *
#*                                                                         *
#*   This program is free software; you can redistribute it and/or modify  *
#*   it under the terms of the GNU General Public License (GPL)            *
#*   as published by the Free Software Foundation; either version 2 of     *
#*   the License, or (at your option) any later version.                   *
#*   for detail see the LICENCE text file.                                 *
#*                                                                         *
#*   FreeCAD is distributed in the hope that it will be useful,            *
#*   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
#*   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
#*   GNU Library General Public License for more details.                  *
#*                                                                         *
#*   You should have received a copy of the GNU Library General Public     *
#*   License along with this plugin; if not, write to the Free Software    *
#*   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
#*   USA                                                                   *
#*                                                                         *
#*   LinObject SAS 2013                                                    *
#***************************************************************************/

# Authors
# Pierre Cosquer <pcosquer@linobject.com>
# Alejandro Galech <agalech@linobject.com>



import os
import shutil
import json
import urllib
import webbrowser
import tempfile


# poster makes it possible to send http request with files
# sudo easy_install poster
from poster.encode import multipart_encode, MultipartParam
import poster.streaminghttp as shttp

import urllib2


import PyQt4.QtGui as qt
from PyQt4 import QtCore

import FreeCAD, FreeCADGui
import Part

connect = QtCore.QObject.connect

def main_window():
    app = qt.qApp
    for x in app.topLevelWidgets():
        if type(x) == qt.QMainWindow:
            return x

def save(gdoc):
    FreeCADGui.runCommand("Std_Save")
    gdoc.Label = os.path.splitext(os.path.basename(gdoc.FileName))[0] or gdoc.Label

def close(gdoc):
    FreeCADGui.runCommand("Std_CloseActiveWindow")
    gdoc2 = FreeCAD.ActiveDocument
    if gdoc == gdoc2:
        FreeCAD.closeDocument(gdoc.Name)

class OpenPLMPluginInstance(object):

    #: location of openPLM server
    SERVER = "http://localhost:8000/"
    #: OpenPLM main directory
    OPENPLM_DIR = os.path.expanduser("~/.openplm")
    #: directory where files are stored
    PLUGIN_DIR = os.path.join(OPENPLM_DIR, "freecad")
    #: gedit plugin configuration file
    CONF_FILE = os.path.join(PLUGIN_DIR, "conf.json")

    def __init__(self):
        self.opener = urllib2.build_opener(shttp.StreamingHTTPHandler(),
                                           shttp.StreamingHTTPRedirectHandler(),
                                           shttp.StreamingHTTPSHandler(),
                                           urllib2.HTTPCookieProcessor())
        self.opener.addheaders = [('User-agent', 'openplm')]
        self.username = ""
        self.connected = False
        self.documents = {}
        self.disable_menuitems()

        data = self.get_conf_data()
        if "server" in data:
            type(self).SERVER = data["server"]

        try:
            os.makedirs(self.PLUGIN_DIR, 0700)
        except os.error:
            pass

        self.window = main_window()

    def disable_menuitems(self):
        self.connected = False
        FreeCADGui.updateGui()

    def enable_menuitems(self):
        self.connected = True
        FreeCADGui.updateGui()

    def login(self, username, password):
        """
        Open a login dialog and connect the user
        """

        self.username = username
        self.password = password

        data = dict(username=self.username, password=self.password)
        res = self.get_data("api/login/", data)
        if res["result"] == "ok":
            #self._action_group2.set_sensitive(True)
            self.load_managed_files()
            self.enable_menuitems()
        else:
            self.disable_menuitems()
            raise ValueError(res["error"])

    def create(self, data, filename, unlock):
        res = self.get_data("api/create/", data)
        if not filename:
            return False, "Bad file name"
        if res["result"] != "ok":
            return False, res["error"]
        else:
            doc = res["object"]
            # create a new doc
            rep = os.path.join(self.PLUGIN_DIR, doc["type"], doc["reference"],
                               doc["revision"])
            try:
                os.makedirs(rep, 0700)
            except os.error:
                # directory already exists, just ignores the exception
                pass
            gdoc = FreeCAD.ActiveDocument
            filename = filename.decode("utf8")
            path = os.path.join(rep, filename)
            fileName, fileExtension = os.path.splitext(filename)
            path_stp=os.path.join(rep, (fileName+".stp")).encode("utf-8")
            #create temporal file stp
            Part.export(gdoc.Objects, path_stp)
            gdoc.FileName = path
            save(gdoc)

            #upload stp and freecad object
            doc_step_file=self.upload_file(doc, path_stp)
            doc_file = self.upload_file(doc, path.encode("utf-8"))

            #remove temporal file stp
            os.remove(path_stp)

            self.add_managed_file(doc, doc_file, path)
            self.load_file(doc, doc_file["id"], path, gdoc)
            if not unlock:
                self.get_data("api/object/%s/lock/%s/" % (doc["id"], doc_file["id"]))
                self.get_data("api/object/%s/lock/%s/" % (doc["id"], doc_step_file["id"]))
            else:
                self.send_thumbnail(gdoc)
                self.forget(gdoc)
            return True, ""

    def get_data(self, url, data=None, show_errors=True, reraise=False):
        data_enc = urllib.urlencode(data) if data else None
        try:
            return json.load(self.opener.open(self.SERVER + url, data_enc))
        except urllib2.URLError as e:
            if show_errors:
                message = e.reason if hasattr(e, "reason") else ""
                if not isinstance(message, basestring):
                    message = str(e)
                show_error(u"Can not open '%s':>\n\t%s" % \
                           (url, unicode(message, "utf-8")), self.window)
            if reraise:
                raise
            else:
                return {"result" : "error", "error" : ""}

    def upload_file(self, doc, path):
        url = self.SERVER + "api/object/%s/add_file/" % doc["id"]
        return self.upload(url, path)["doc_file"]

    def upload(self, url, path):
        if isinstance(path, unicode):
            name = path
            path = path.encode("utf-8")
        else:
            name = path.decode("utf-8")
        with open(path, "rb") as f:
            mp = MultipartParam("filename", fileobj=f, filename=name)
            datagen, headers = multipart_encode({"filename": mp})
            # Create the Request object
            request = urllib2.Request(url, datagen, headers)
            res = json.load(self.opener.open(request))
        return res

    def download(self, doc, doc_file):

        f = self.opener.open(self.SERVER + "file/%s/" % doc_file["id"])
        rep = os.path.join(self.PLUGIN_DIR, doc["type"], doc["reference"],
                           doc["revision"])
        try:
            os.makedirs(rep, 0700)
        except os.error:
            # directory already exists, just ignores the exception
            pass
        dst_name = os.path.join(rep, doc_file["filename"])
        dst = open(dst_name.encode("utf-8"), "wb")
        shutil.copyfileobj(f, dst)
        f.close()
        dst.close()
        self.add_managed_file(doc, doc_file, dst_name)
        self.load_file(doc, doc_file["id"], dst_name)

    def attach_to_part(self, doc, part_id):
        res = self.get_data("api/object/%s/attach_to_part/%s/" % (doc["id"], part_id))
        if res["result"] == "ok":
            url = self.SERVER + "object/%s/%s/%s/parts" % (doc["type"],
                    doc["reference"], doc["revision"])
            webbrowser.open_new_tab(url)
        else:
            show_error("Can not attach\n%s" % res.get('error', ''), self.window)

    def check_out(self, doc, doc_file):
        self.get_data("api/object/%s/checkout/%s/" % (doc["id"], doc_file["id"]))
        self.download(doc, doc_file)


        #on va locker fichier step associe
        url= "api/object/%s/files/all/" % doc["id"]
        res = PLUGIN.get_data(url)
        fileName, fileExtension = os.path.splitext(doc_file["filename"])
        doc_step = [obj for obj in res["files"] if obj["filename"] == fileName+".stp"]
        if not len(doc_step)==0:
            self.get_data("api/object/%s/lock/%s/" % (doc["id"], doc_step[0]["id"]))
        #end locker

    def add_managed_file(self, document, doc_file, path):
        data = self.get_conf_data()
        documents = data.get("documents", {})
        doc = documents.get(str(document["id"]), dict(document))
        files = doc.get("files", {})
        files[doc_file["id"]] = path
        doc["files"] = files
        documents[doc["id"]] = doc
        data["documents"] = documents
        self.save_conf(data)

    def save_conf(self, data):
        f = open(self.CONF_FILE, "w")
        json.dump(data, f)
        f.close()

    def get_conf_data(self):
        try:
            with open(self.CONF_FILE, "r") as f:
                try:
                    return json.load(f)
                except ValueError:
                    # empty/bad config file
                    return {}
        except IOError:
            # file does not exist
            return {}

    def set_server(self, url):
        if not url.endswith("/"):
            url += "/"
        data = self.get_conf_data()
        data["server"] = url
        type(self).SERVER = url
        self.save_conf(data)
        if self.username:
            try:
                self.login(self.username, self.password)
            except ValueError:
                pass

    def get_managed_files(self):
        data = self.get_conf_data()
        files = []
        for doc in data.get("documents", {}).itervalues():
            files.extend((d, doc) for d in doc.get("files", {}).items())
        return files

    def forget(self, gdoc=None, delete=True, close_doc=False):
        gdoc = gdoc or FreeCAD.ActiveDocument
        if gdoc and gdoc in self.documents:
            doc = self.documents[gdoc]["openplm_doc"]
            doc_file_id = self.documents[gdoc]["openplm_file_id"]
            path = self.documents[gdoc]["openplm_path"]
            del self.documents[gdoc]
            data = self.get_conf_data()
            del data["documents"][str(doc["id"])]["files"][str(doc_file_id)]
            if not  data["documents"][str(doc["id"])]["files"]:
                del data["documents"][str(doc["id"])]
            self.save_conf(data)
            #on va unlocker
            self.get_data("api/object/%s/unlock/%s/" % (doc["id"], doc_file_id))
            url= "api/object/%s/files/all/" % doc["id"]
            res = PLUGIN.get_data(url)
            root, f_name = os.path.split(path)
            fileName, fileExtension = os.path.splitext(f_name)
            doc_step = [obj for obj in res["files"] if obj["filename"] == fileName+".stp"]
            if doc_step:
                self.get_data("api/object/%s/unlock/%s/" % (doc["id"], doc_step[0]["id"]))

            #end unlocker
            path = path.encode("utf-8")

            if delete and os.path.exists(path):
                os.remove(path)
            if close_doc:
                close(gdoc)

    def load_managed_files(self):
        for (doc_file_id, path), doc in self.get_managed_files():
            self.load_file(doc, doc_file_id, path)

    def load_file(self, doc, doc_file_id, path, gdoc=None):
        try:
            document = gdoc or FreeCAD.openDocument(path.encode("utf-8"))
        except IOError:
            show_error("Can not load %s" % path, self.window)
            return
        self.documents[document] = dict(openplm_doc=doc,
            openplm_file_id=doc_file_id, openplm_path=path)
        if " rev. " not in document.Label:
            document.Label = document.Label + " / %(name)s rev. %(revision)s" % doc
        return document

    def check_in(self, gdoc, unlock, save_file=True):
        if gdoc and gdoc in self.documents:
            doc = self.documents[gdoc]["openplm_doc"]
            doc_file_id = self.documents[gdoc]["openplm_file_id"]
            #doc_file_name = self.documents[gdoc]["openplm_file_name"]
            path = self.documents[gdoc]["openplm_path"]
            def func():

                #check-in fichier step asscocies if exists
                #api/doc_id/files/[all/]
                url= "api/object/%s/files/all/" % doc["id"]
                res = PLUGIN.get_data(url)
                root, f_name = os.path.split(path)
                fileName, fileExtension = os.path.splitext(f_name)
                doc_step = [obj for obj in res["files"] if obj["filename"] == fileName+".stp"]

                fileName, fileExtension = os.path.splitext(path)
                path_stp= (fileName + ".stp").encode("utf-8")
                Part.export(gdoc.Objects, path_stp)

                if not doc_step:    #il faut generer un nouvelle fichier step
                    doc_step_file=self.upload_file(doc,path_stp) # XXX
                    doc_step.append(doc_step_file)
                else:                   #il faut un check-in
                    url = self.SERVER + "api/object/%s/checkin/%s/" % (doc["id"], doc_step[0]["id"]) # XXX
                    self.upload(url, path_stp)
                    os.remove(path_stp)

                url = self.SERVER + "api/object/%s/checkin/%s/" % (doc["id"], doc_file_id) # XXX
                self.upload(url, path)

                if not unlock:
                    self.get_data("api/object/%s/lock/%s/" % (doc["id"], doc_file_id)) # XXX
                    if doc_step:
                        self.get_data("api/object/%s/lock/%s/" % (doc["id"], doc_step[0]["id"])) # XXX
                else:
                    self.send_thumbnail(gdoc)
                    self.forget(gdoc)
            if save_file:
                save(gdoc)
                func()
            else:
                func()
        else:
            show_error('Can not check in : file not in openPLM', self.window)

    def send_thumbnail(self, gdoc):
        doc = self.documents[gdoc]["openplm_doc"]
        doc_file_id = self.documents[gdoc]["openplm_file_id"]
        view = FreeCADGui.ActiveDocument.ActiveView
        f = tempfile.NamedTemporaryFile(suffix=".png")
        view.saveImage(f.name)
        datagen, headers = multipart_encode({"filename": open(f.name, "rb")})
        # Create the Request object
        url = self.SERVER + "api/object/%s/add_thumbnail/%s/" % (doc["id"], doc_file_id)
        request = urllib2.Request(url, datagen, headers)
        res = self.opener.open(request)
        f.close()

    def revise(self, gdoc, revision, unlock):
        if gdoc and gdoc in self.documents:
            doc = self.documents[gdoc]["openplm_doc"]
            doc_file_id = self.documents[gdoc]["openplm_file_id"]
            path = self.documents[gdoc]["openplm_path"]
            res = self.get_data("api/object/%s/revise/" % doc["id"],
                                {"revision" : revision})
            new_doc = res["doc"]
            name = os.path.basename(gdoc.FileName)
            doc_file = None
            for f in res["files"]:
                if f["filename"] == name:
                    doc_file = f
                    break
            # create a new doc
            rep = os.path.join(self.PLUGIN_DIR, doc["type"], doc["reference"],
                               revision)
            try:
                os.makedirs(rep, 0700)
            except os.error:
                # directory already exists, just ignores the exception
                pass

            self.forget(gdoc, close_doc=False)
            path = os.path.join(rep, name)
            gdoc.FileName = path
            save(gdoc)
            self.load_file(new_doc, doc_file["id"], path, gdoc)
            self.add_managed_file(new_doc, doc_file, path)
            self.check_in(gdoc, unlock, False)
            self.get_data("api/object/%s/unlock/%s/" % (doc["id"], doc_file_id))
        else:
            show_error("Can not revise : file not in openPLM", self.window)

    def check_is_locked(self, doc_id, file_id, error_dialog=True):
        """
        Return True if file which is is *file_id* is locked.

        If it is unlocked and *error_dialog* is True, an ErrorDialog is
        displayed
        """
        locked = self.get_data("api/object/%s/islocked/%s/" % (doc_id, file_id))["locked"]
        if not locked and error_dialog:
            show_error("File is not locked, action not allowed", self.window)
        return locked


PLUGIN = OpenPLMPluginInstance()

def show_error(message, parent):
    dialog = qt.QMessageBox()
    dialog.setText(message)
    dialog.setWindowTitle("Error")
    dialog.setIcon(qt.QMessageBox.Warning)
    dialog.exec_()

BANNER_PATH = os.path.join(os.path.dirname(__file__), "banner_openplm.png")
class Dialog(qt.QDialog):

    TITLE = "..."
    ACTION_NAME = "..."

    def __init__(self):
        qt.QDialog.__init__(self)
        self.instance = PLUGIN
        self.setWindowTitle(self.TITLE)
        box = qt.QVBoxLayout()
        self.vbox = qt.QVBoxLayout()
        banner = qt.QLabel()
        picture = qt.QPixmap(BANNER_PATH)
        banner.setPixmap(picture)
        box.addWidget(banner)
        box.addLayout(self.vbox)
        box.setMargin(0)
        self.vbox.setMargin(12)
        self.setLayout(box)
        self.update_ui()

    def get_value(self, entry, field=None):
        value = None
        if isinstance(entry, qt.QLineEdit):
            value = unicode(entry.text()).encode("utf-8")
        elif isinstance(entry, qt.QComboBox):
            if not field:
                value = unicode(entry.currentText()).encode("utf-8")
            else:
                value = field["choices"][entry.currentIndex()][0]
        elif isinstance(entry, qt.QCheckBox):
            value = entry.isChecked()
        return value

    def set_value(self, entry, value, field=None):
        if isinstance(entry, qt.QLineEdit):
            if isinstance(value, str):
                value = value.decode("utf-8")
            entry.setText(value or '')
        elif isinstance(entry, qt.QComboBox):
            choices = [c[0] for c in field["choices"]]
            if isinstance(value, str):
                value = value.decode("utf-8")
            entry.setCurrentIndex(choices.index(value or ''))
        elif isinstance(entry, qt.QCheckBox):
            entry.setChecked(value)

    def field_to_widget(self, field):
        widget = None
        attributes = {}
        if field["type"] in ("text", "int", "decimal", "float"):
            widget = qt.QLineEdit()
        elif field["type"] == "boolean":
            widget = qt.QCheckBox()
        elif field["type"] == "choice":
            widget = qt.QComboBox()
            choices = field["choices"]
            if [u'', u'---------'] not in choices:
                choices = ([u'', u'---------'],) + tuple(choices)
            field["choices"] = choices
            values = []
            for _, c in choices:
                values.append(c)
            widget.addItems(values)
        if type == "":
            raise ValueError()
        self.set_value(widget, field["initial"], field)
        return widget

    def update_ui(self):
        pass

class LoginDialog(Dialog):
    TITLE = 'Login'

    def update_ui(self):
        table = qt.QGridLayout()
        label = qt.QLabel(self)
        label.setText('Username:')
        table.addWidget(label, 0, 0)
        label = qt.QLabel(self)
        label.setText('Password:')
        table.addWidget(label, 1, 0)
        self.user_entry = qt.QLineEdit(self)
        table.addWidget(self.user_entry, 0, 1)
        self.pw_entry = qt.QLineEdit()
        self.pw_entry.setEchoMode(qt.QLineEdit.Password)
        table.addWidget(self.pw_entry, 1, 1)

        self.vbox.addLayout(table)
        buttons = qt.QDialogButtonBox.Ok | qt.QDialogButtonBox.Cancel
        buttons_box = qt.QDialogButtonBox(buttons, parent=self)
        connect(buttons_box, QtCore.SIGNAL("accepted()"), self.login)
        connect(buttons_box, QtCore.SIGNAL("rejected()"), self.reject)

        self.vbox.addWidget(buttons_box)

    def login(self):
        username = self.user_entry.text()
        password = self.pw_entry.text()
        try:
            PLUGIN.login(username, password)
            self.accept()
        except ValueError, e:
            self.user_entry.setFocus()
            show_error("Can not login: %s" % str(e), self)

class ConfigureDialog(Dialog):

    TITLE = "Configure"

    def update_ui(self):

        table = qt.QGridLayout()
        label = qt.QLabel()
        label.setText("OpenPLM server's location:")
        self.url_entry = qt.QLineEdit()
        self.url_entry.setText(PLUGIN.SERVER)
        table.addWidget(label, 0, 0)
        table.addWidget(self.url_entry, 0, 1)

        self.vbox.addLayout(table)
        buttons = qt.QDialogButtonBox.Ok | qt.QDialogButtonBox.Cancel
        buttons_box = qt.QDialogButtonBox(buttons, parent=self)
        connect(buttons_box, QtCore.SIGNAL("accepted()"), self.action_cb)
        connect(buttons_box, QtCore.SIGNAL("rejected()"), self.reject)
        self.vbox.addWidget(buttons_box)

    def action_cb(self):
        self.accept()
        url = self.get_value(self.url_entry, None)
        PLUGIN.set_server(url)

class SearchDialog(Dialog):

    TITLE = "Search"
    ACTION_NAME = "..."
    TYPE = "Document"
    SEARCH_SUFFIX = ""
    TYPES_URL = "api/docs/"
    ALL_FILES = False
    EXPAND_FILES = True

    def update_ui(self):

        docs = PLUGIN.get_data(self.TYPES_URL)
        self.types = docs["types"]

        table = qt.QGridLayout()
        self.vbox.addLayout(table)
        self.type_entry = qt.QComboBox()
        self.type_entry.addItems(self.types)
        self.type_entry.setCurrentIndex(self.types.index(self.TYPE))
        connect(self.type_entry, QtCore.SIGNAL("activated(const QString&)"),
                self.type_entry_activate_cb)
        self.name_entry = qt.QLineEdit()
        self.rev_entry = qt.QLineEdit()
        self.fields = [("type", self.type_entry),
                      ]
        for i, (text, entry) in enumerate(self.fields):
            label = qt.QLabel()
            label.setText(text.capitalize()+":")
            table.addWidget(label, i, 0)
            table.addWidget(entry, i, 1)

        self.advanced_table = qt.QGridLayout()
        self.advanced_fields = []
        self.vbox.addLayout(self.advanced_table)
        self.display_fields(self.TYPE)

        search_button = qt.QPushButton("Search")
        connect(search_button, QtCore.SIGNAL("clicked()"), self.search)
        self.vbox.addWidget(search_button)

        self.results_box = qt.QVBoxLayout()
        self.vbox.addLayout(self.results_box)

        self.tree = qt.QTreeWidget()
        self.tree.setColumnCount(1)
        self.tree.setHeaderLabel("Results")
        self.results_box.addWidget(self.tree)
        connect(self.tree, QtCore.SIGNAL("itemExpanded(QTreeWidgetItem *)"),
                                         self.expand)

        self.action_button = qt.QPushButton(self.ACTION_NAME)
        connect(self.action_button, QtCore.SIGNAL("clicked()"), self.action_cb)
        self.results_box.addWidget(self.action_button)

    def type_entry_activate_cb(self, typename):
        self.display_fields(typename)

    def display_fields(self, typename):
        fields = self.instance.get_data("api/search_fields/%s/" % typename)["fields"]
        temp = {}
        for field, entry in self.advanced_fields:
            temp[field["name"]] = self.get_value(entry, field)
        while self.advanced_table.count():
            child = self.advanced_table.itemAt(0).widget()
            self.advanced_table.removeWidget(child)
            child.hide()
            child.destroy()
        self.advanced_table.invalidate()
        self.advanced_fields = []
        for i, field in enumerate(fields):
            text = field["label"]
            label = qt.QLabel()
            label.setText(text.capitalize()+":")
            self.advanced_table.addWidget(label, i, 0)
            widget = self.field_to_widget(field)
            if field["name"] in temp:
                self.set_value(widget, temp[field["name"]], field)
            self.advanced_table.addWidget(widget, i, 1)
            self.advanced_fields.append((field, widget))

    def action_cb(self):
        node = self.tree.currentItem()
        if not node:
            return
        doc = self.nodes[node.parent()]
        doc_file = doc["files"][node.parent().indexOfChild(node)]
        del doc["files"]
        self.do_action(doc, doc_file)

    def expand(self, item):
        res = self.nodes[item]
        suffix = "all/" if self.ALL_FILES else ""
        url = "api/object/%s/files/%s" % (res["id"], suffix)
        files = PLUGIN.get_data(url)["files"]
        if "files" in res:
            return
        res["files"] = files
        item.removeChild(item.child(0))
        for f in files:
            node = qt.QTreeWidgetItem([f["filename"]])
            item.addChild(node)
        if not files:
            node = qt.QTreeWidgetItem(["No file attached to document"])
            item.addChild(node)

    def display_results(self, results):
        self.nodes = {}
        self.tree.clear()
        self.tree.reset()
        for i, res in enumerate(results):
            text = "%(reference)s|%(type)s|%(revision)s : %(name)s" % res
            node = qt.QTreeWidgetItem([text])
            if self.EXPAND_FILES:
                child = qt.QTreeWidgetItem(["..."])
                node.addChild(child)
            node.setExpanded(False)
            self.tree.insertTopLevelItem(i, node)
            self.nodes[node] = res

    def search(self, *args):
        data = {}
        for text, entry in self.fields:
            value = self.get_value(entry, None)
            if value:
                data[text] = value
        for field, entry in self.advanced_fields:
            value = self.get_value(entry, field)
            if value:
                data[field["name"]] = value
        get = urllib.urlencode(data)
        self.display_results(PLUGIN.get_data("api/search/%s?%s" % (self.SEARCH_SUFFIX, get))["objects"])

    def do_action(self, doc, doc_file):
        print doc, doc_file

class CheckOutDialog(SearchDialog):
    TITLE = "Check-out..."
    ACTION_NAME = "Check-out"

    def do_action(self, doc, doc_file):
        PLUGIN.check_out(doc, doc_file)
        self.accept()

class DownloadDialog(SearchDialog):
    TITLE = "Download..."
    ACTION_NAME = "Download"
    SEARCH_SUFFIX = "false/true/"
    ALL_FILES = True

    def do_action(self, doc, doc_file):
        PLUGIN.download(doc, doc_file)
        self.accept()

class CheckInDialog(Dialog):

    TITLE = "Check-in..."
    ACTION_NAME = "Check-in"

    def __init__(self, doc, name):
        self.doc = doc
        self.name = name
        Dialog.__init__(self)

    def update_ui(self):
        text = "%s|%s|%s" % (self.doc["reference"], self.doc["revision"],
                                       self.doc["type"])

        label = qt.QLabel(text)
        self.vbox.addWidget(label)
        self.unlock_button = qt.QCheckBox('Unlock ?')
        self.vbox.addWidget(self.unlock_button)

        button = qt.QPushButton(self.ACTION_NAME)
        connect(button, QtCore.SIGNAL("clicked()"), self.action_cb)
        self.vbox.addWidget(button)

    def action_cb(self):
        doc = FreeCAD.ActiveDocument
        unlock = self.get_value(self.unlock_button, None)
        PLUGIN.check_in(doc, unlock)
        self.accept()

class ReviseDialog(Dialog):

    TITLE = "Revise..."
    ACTION_NAME = "Revise"

    def __init__(self, doc, name, revision):
        self.doc = doc
        self.name = name
        self.revision = revision
        self.gdoc = None
        Dialog.__init__(self)

    def update_ui(self):
        hbox = qt.QHBoxLayout()
        text = "%s|" % self.doc["reference"]
        label = qt.QLabel(text)
        hbox.addWidget(label)
        self.revision_entry = qt.QLineEdit()
        self.revision_entry.setText(self.revision)
        hbox.addWidget(self.revision_entry)
        text = "|%s" % self.doc["type"]
        label = qt.QLabel(text)
        hbox.addWidget(label)
        self.vbox.addLayout(hbox)
        self.unlock_button = qt.QCheckBox('Unlock ?')
        self.vbox.addWidget(self.unlock_button)
        text = "Warning: old revision file will be automatically unlocked!"
        label = qt.QLabel(text)
        self.vbox.addWidget(label)

        button = qt.QPushButton(self.ACTION_NAME)
        connect(button, QtCore.SIGNAL("clicked()"), self.action_cb)
        self.vbox.addWidget(button)

    def action_cb(self):
        doc = FreeCAD.ActiveDocument
        self.gdoc = PLUGIN.revise(doc,
                          self.get_value(self.revision_entry, None),
                          self.get_value(self.unlock_button, None))
        self.accept()

class AttachToPartDialog(SearchDialog):
    TITLE = "Attach to part"
    ACTION_NAME = "Attach"
    SEARCH_SUFFIX = "false/"
    TYPE = "Part"
    TYPES_URL = "api/parts/"
    EXPAND_FILES = False

    def __init__(self, doc):
        SearchDialog.__init__(self)
        self.doc = doc

    def do_action(self, part):
        PLUGIN.attach_to_part(self.doc, part["id"])
        self.accept()

    def action_cb(self):
        node =  self.tree.currentItem()
        if not node:
            return
        doc = self.nodes[node]
        self.do_action(doc)

class CreateDialog(SearchDialog):

    TITLE = "Create a document..."
    ACTION_NAME = "Create"
    TYPE = "Document"
    TYPES_URL = "api/docs/"

    def update_ui(self):
        self.doc_created = None
        docs = PLUGIN.get_data(self.TYPES_URL)
        self.types = docs["types"]

        table = qt.QGridLayout()
        self.vbox.addLayout(table)
        self.type_entry = qt.QComboBox()
        self.type_entry.addItems(self.types)
        self.type_entry.setCurrentIndex(self.types.index(self.TYPE))
        connect(self.type_entry, QtCore.SIGNAL("activated(const QString&)"),
                self.type_entry_activate_cb)
        self.fields = [("type", self.type_entry),
                      ]
        for i, (text, entry) in enumerate(self.fields):
            label = qt.QLabel()
            label.setText(text.capitalize()+":")
            table.addWidget(label, i, 0)
            table.addWidget(entry, i, 1)

        self.advanced_table = qt.QGridLayout()
        self.advanced_fields = []
        self.vbox.addLayout(self.advanced_table)
        self.display_fields(self.TYPE)

        hbox = qt.QHBoxLayout()
        label = qt.QLabel()
        label.setText("Filename:")
        hbox.addWidget(label)
        self.filename_entry = qt.QLineEdit()
        hbox.addWidget(self.filename_entry)
        doc = FreeCAD.ActiveDocument
        self.filename_entry.setText(os.path.basename(doc.FileName) or "x.fcstd")
        self.vbox.addLayout(hbox)
        self.unlock_button = qt.QCheckBox('Unlock ?')
        self.vbox.addWidget(self.unlock_button)

        self.action_button = qt.QPushButton(self.ACTION_NAME)
        connect(self.action_button, QtCore.SIGNAL("clicked()"), self.action_cb)
        self.vbox.addWidget(self.action_button)

    def type_entry_activate_cb(self, typename):
        self.display_fields(typename)

    def display_fields(self, typename):
        fields = self.instance.get_data("api/creation_fields/%s/" % typename)["fields"]
        temp = {}
        for field, entry in self.advanced_fields:
            temp[field["name"]] = self.get_value(entry, field)
        while self.advanced_table.count():
            child = self.advanced_table.itemAt(0).widget()
            self.advanced_table.removeWidget(child)
            child.hide()
            child.destroy()
        self.advanced_table.invalidate()
        self.advanced_fields = []
        for i, field in enumerate(fields):
            text = field["label"]
            label = qt.QLabel()
            label.setText(text.capitalize()+":")
            self.advanced_table.addWidget(label, i, 0)
            widget = self.field_to_widget(field)
            if field["name"] in temp:
                self.set_value(widget, temp[field["name"]], field)
            self.advanced_table.addWidget(widget, i, 1)
            self.advanced_fields.append((field, widget))

    def action_cb(self):
        data = self.get_creation_data()
        b, error = PLUGIN.create(self.get_creation_data(),
                                 self.get_value(self.filename_entry, None),
                                 self.get_value(self.unlock_button, None))
        if b:
            self.accept()
        else:
            show_error(error, self)
        self.doc_created = b

    def get_creation_data(self):
        data = {}
        for field_name, widget in self.fields:
            data[field_name] = self.get_value(widget, None)
        for field, widget in self.advanced_fields:
            data[field["name"]] = self.get_value(widget, field)
        return data


class OpenPLMLogin:

    def Activated(self):
        dialog = LoginDialog()
        dialog.exec_()

    def GetResources(self):
        return {'MenuText': 'Login', 'ToolTip': 'Login'}

FreeCADGui.addCommand('OpenPLM_Login', OpenPLMLogin())

class OpenPLMConfigure:

    def Activated(self):
        dialog = ConfigureDialog()
        dialog.exec_()

    def GetResources(self):
        return {'Pixmap' : 'preferences-system', 'MenuText': 'Configure', 'ToolTip': 'Configure'}

FreeCADGui.addCommand('OpenPLM_Configure', OpenPLMConfigure())

class OpenPLMCheckOut:

    def Activated(self):
        dialog = CheckOutDialog()
        dialog.exec_()

    def GetResources(self):
        return {'MenuText': 'Check-out', 'ToolTip': 'Check-out'}

    def IsActive(self):
        return PLUGIN.connected

FreeCADGui.addCommand('OpenPLM_CheckOut', OpenPLMCheckOut())


class OpenPLMDownload:

    def Activated(self):
        dialog = DownloadDialog()
        dialog.exec_()

    def GetResources(self):
        return {'MenuText': 'Download', 'ToolTip': 'Download'}

    def IsActive(self):
        return PLUGIN.connected

FreeCADGui.addCommand('OpenPLM_Download', OpenPLMDownload())

class OpenPLMForget:

    def Activated(self):
        PLUGIN.forget(close_doc=True)

    def GetResources(self):
        return {'MenuText': 'Forget current file',
                'ToolTip': 'Forget and delete current file'}

    def IsActive(self):
        return PLUGIN.connected and FreeCAD.ActiveDocument in PLUGIN.documents

FreeCADGui.addCommand('OpenPLM_Forget', OpenPLMForget())

class OpenPLMCheckIn:

    def Activated(self):
        gdoc = FreeCAD.ActiveDocument
        if gdoc and gdoc in PLUGIN.documents:
            doc = PLUGIN.documents[gdoc]["openplm_doc"]
            doc_file_id = PLUGIN.documents[gdoc]["openplm_file_id"]
            path = PLUGIN.documents[gdoc]["openplm_path"]
            if not doc or not PLUGIN.check_is_locked(doc["id"], doc_file_id):
                return
            name = os.path.basename(path)
            dialog = CheckInDialog(doc, name)
            dialog.exec_()
            if gdoc not in PLUGIN.documents:
                close(gdoc)
        else:
            win = main_window()
            show_error("Document not stored in OpenPLM", win)

    def GetResources(self):
        return {'MenuText': 'Check-in', 'ToolTip': 'Check-in'}

    def IsActive(self):
        return PLUGIN.connected and FreeCAD.ActiveDocument in PLUGIN.documents

FreeCADGui.addCommand('OpenPLM_CheckIn', OpenPLMCheckIn())

class OpenPLMRevise:

    def Activated(self):
        gdoc = FreeCAD.ActiveDocument
        if gdoc and gdoc in PLUGIN.documents:
            doc = PLUGIN.documents[gdoc]["openplm_doc"]
            doc_file_id = PLUGIN.documents[gdoc]["openplm_file_id"]
            path = PLUGIN.documents[gdoc]["openplm_path"]
            if not doc or not PLUGIN.check_is_locked(doc["id"], doc_file_id):
                return
            revisable = PLUGIN.get_data("api/object/%s/isrevisable/" % doc["id"])["revisable"]
            if not revisable:
                win = main_window()
                show_error("Document can not be revised", win)
                return
            res = PLUGIN.get_data("api/object/%s/nextrevision/" % doc["id"])
            revision = res["revision"]
            name = os.path.basename(path)
            dialog = ReviseDialog(doc, name, revision)
            dialog.exec_()
            if gdoc not in PLUGIN.documents:
                close(gdoc)
        else:
            win = main_window()
            show_error("Document not stored in OpenPLM", win)

    def GetResources(self):
        return {'MenuText': 'Revise', 'ToolTip': 'Revise'}

    def IsActive(self):
        return PLUGIN.connected and FreeCAD.ActiveDocument in PLUGIN.documents

FreeCADGui.addCommand('OpenPLM_Revise', OpenPLMRevise())

class OpenPLMAttach:

    def Activated(self):
        gdoc = FreeCAD.ActiveDocument
        if gdoc and gdoc in PLUGIN.documents:
            doc = PLUGIN.documents[gdoc]["openplm_doc"]
            dialog = AttachToPartDialog(doc)
            dialog.exec_()
        else:
            win = main_window()
            show_error("Document not stored in OpenPLM", win)

    def GetResources(self):
        return {'MenuText': 'Attach to a part',
                'ToolTip': 'Attach to a part'}

    def IsActive(self):
        return PLUGIN.connected and FreeCAD.ActiveDocument in PLUGIN.documents

FreeCADGui.addCommand('OpenPLM_AttachToPart', OpenPLMAttach())

class OpenPLMCreate:

    def Activated(self):
        gdoc = FreeCAD.ActiveDocument
        win = main_window()
        if not gdoc:
            show_error("Need an opened file to create a document", win)
            return
        if gdoc in PLUGIN.documents:
            show_error("Current file already attached to a document", win)
            return
        dialog = CreateDialog()
        resp = dialog.exec_()
        if dialog.doc_created and gdoc not in PLUGIN.documents:
            close(gdoc)

    def GetResources(self):
        return {'Pixmap' : 'document-new', 'MenuText': 'Create a Document',
                'ToolTip': 'Create a document'}

    def IsActive(self):
        doc = FreeCAD.ActiveDocument
        return PLUGIN.connected and doc and doc not in PLUGIN.documents

FreeCADGui.addCommand('OpenPLM_Create', OpenPLMCreate())

def build_menu():
    win = main_window()
    mb =  win.menuBar()
    menu = mb.addMenu("OpenPLM")
    for cls in (OpenPLMLogin, OpenPLMCheckOut):
        cmd = cls()
        action = qt.QAction(cmd.GetResources()["MenuText"], None)
        QtCore.QObject.connect(action, QtCore.SIGNAL("triggered"), cmd.Activated)
        menu.addAction(action)
    menu.show()

