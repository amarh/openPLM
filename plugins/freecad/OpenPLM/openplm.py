import os
import shutil
import json
import urllib
import webbrowser

# poster makes it possible to send http request with files
# sudo easy_install poster
from poster.encode import multipart_encode
from poster.streaminghttp import StreamingHTTPRedirectHandler, StreamingHTTPHandler

import urllib2

import traceback

import PyQt4.QtGui as qt
from PyQt4 import QtCore, QtGui

import FreeCAD, FreeCADGui

connect = QtCore.QObject.connect

def close(gdoc, desktop):
    enum = desktop.getComponents().createEnumeration()
    cpt = 0
    while enum.hasMoreElements():
        cpt += 1
        enum.nextElement()
    gdoc.setModified(False)
    if cpt == 1:
        name = "_default"
        type = doc_to_type(gdoc)
        desktop.loadComponentFromURL("private:factory/" + type, name,
                                     CREATE | ALL, ())
    try:
        gdoc.close(True)
    except CloseVetoException:
        pass

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
        
        self.opener = urllib2.build_opener(StreamingHTTPHandler(),
                                           StreamingHTTPRedirectHandler(),
                                           urllib2.HTTPCookieProcessor())
        self.username = ""
        self.desktop = None
        self.documents = {}
        self.disable_menuitems()

        data = self.get_conf_data()
        if "server" in data:
            type(self).SERVER = data["server"]

        try:
            os.makedirs(self.OPENPLM_DIR, 0700)
        except os.error:
            pass

    def set_desktop(self, desktop):
        self.desktop = desktop
        self.window = desktop.getCurrentFrame().ContainerWindow

    def disable_menuitems(self):
        pass

    def enable_menuitems(self):
        pass

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
            gdoc = self.desktop.getCurrentComponent()
            path = os.path.join(rep, filename)
            gdoc.storeAsURL("file://" + path, ())
            doc_file = self.upload_file(doc, path)
            self.add_managed_file(doc, doc_file, path)
            self.load_file(doc, doc_file["id"], path)
            if not unlock:
                self.get_data("api/object/%s/lock/%s/" % (doc["id"], doc_file["id"]))
            else:
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
        datagen, headers = multipart_encode({"filename": open(path, "rb")})
        # Create the Request object
        request = urllib2.Request(url, datagen, headers)
        res = json.load(self.opener.open(request))
        return res["doc_file"]

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
        dst = open(dst_name, "wb")
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
        gdoc = gdoc or self.desktop.getCurrentComponent()
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
            if delete and os.path.exists(path):
                os.remove(path)
            if close_doc:
                close(gdoc, self.desktop)

    def load_managed_files(self):
        for (doc_file_id, path), doc in self.get_managed_files():
            self.load_file(doc, doc_file_id, path)

    def load_file(self, doc, doc_file_id, path):
        document = FreeCAD.openDocument(path)
        if not document:
            show_error("Can not load %s" % path, self.window)
            return
        self.documents[document] = dict(openplm_doc=doc,
            openplm_file_id=doc_file_id, openplm_path=path)
        #document.setTitle(document.getTitle() + " / %(name)s rev. %(revision)s" % doc)
        return document

    def check_in(self, gdoc, unlock, save=True):
        if gdoc and gdoc in self.documents:
            doc = self.documents[gdoc]["openplm_doc"]
            doc_file_id = self.documents[gdoc]["openplm_file_id"]
            path = self.documents[gdoc]["openplm_path"]
            def func():
                # headers contains the necessary Content-Type and Content-Length>
                # datagen is a generator object that yields the encoded parameters
                datagen, headers = multipart_encode({"filename": open(path, "rb")})
                # Create the Request object
                url = self.SERVER + "api/object/%s/checkin/%s/" % (doc["id"], doc_file_id)
                request = urllib2.Request(url, datagen, headers)
                res = self.opener.open(request)
                if not unlock:
                    self.get_data("api/object/%s/lock/%s/" % (doc["id"], doc_file_id))
                else:
                    self.forget(gdoc)
            if save:
                gdoc.store()
                func()
            else:
                func()
        else:
            show_error('Can not check in : file not in openPLM', self.window)

    def revise(self, gdoc, revision, unlock):
        if gdoc and gdoc in self.documents:
            doc = self.documents[gdoc]["openplm_doc"]
            doc_file_id = self.documents[gdoc]["openplm_file_id"]
            path = self.documents[gdoc]["openplm_path"]
            res = self.get_data("api/object/%s/revise/" % doc["id"],
                                {"revision" : revision})
            new_doc = res["doc"]
            name = os.path.basename(gdoc)
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
            
            gdoc.store()
            new_path = os.path.join(rep, name)
            shutil.move(path, new_path)
            self.forget(gdoc, delete=False)
            gd = self.load_file(new_doc, doc_file["id"], new_path)
            self.add_managed_file(new_doc, doc_file, new_path)
            self.check_in(gd, unlock, False)
            self.get_data("api/object/%s/unlock/%s/" % (doc["id"], doc_file_id))
            return gd
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
    dialog = qt.QErrorMessage(parent)
    dialog.showMessage(message)
    dialog.exec_()

class Dialog(qt.QDialog):

    TITLE = "..."
    ACTION_NAME = "..."

    WIDTH = 200
    HEIGHT = 300
    PAD = 5
    ROW_HEIGHT = 15
    ROW_PAD = 2
    
    def __init__(self):
        qt.QDialog.__init__(self)
        self.setWindowTitle(self.TITLE)
        self.vbox = qt.QVBoxLayout()
        self.setLayout(self.vbox)
        self.instance = PLUGIN
        self.update_ui()

    def get_value(self, entry, field=None):
        value = None
        if isinstance(entry, qt.QLineEdit):
            value = unicode(entry.text(), "utf-8")
        elif isinstance(entry, qt.QComboBox):
            if not field:
                value = unicode(entry.currentText(), "utf-8")
            else:
                value = field["choices"][entry.currentIndex()][0]
        elif isinstance(entry, qt.QCheckBox):
            value = entry.isChecked()
        return value

    def set_value(self, entry, value, field=None):
        if isinstance(entry, qt.QLineEdit):
            entry.setText(value or '')
        elif isinstance(entry, qt.QComboBox):
            choices = [c[0] for c in field["choices"]]
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

    def actionPerformed(self, actionEvent):
        pass

class LoginDialog(Dialog):
    HEIGHT = 105
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
        #self.user_entry.connect("activate", self.user_entry_activate_cb)
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
            show_error("Can not login: %s" % str(e), self)

class ConfigureDialog(Dialog):

    TITLE = "Conffigure"
    HEIGHT = 105

    def run(self):
        label = self.addWidget('url', 'FixedText', 5, 10, 60, 14,
                               Label="OpenPLM server's location:")
        self.url_entry = self.addWidget('UrlEntry', 'Edit', 90, 10, 100, 14)
        self.url_entry.Text = PLUGIN.SERVER

        button = self.addWidget('configure', 'Button', 55, 85, 50, 14,
                                Label='Configure')
        self.container = smgr.createInstanceWithContext(
            'com.sun.star.awt.UnoControlDialog', )
        self.container.setModel(self.dialog)
        self.container.getControl('configure').addActionListener(self)
        toolkit = smgr.createInstanceWithContext(
            'com.sun.star.awt.ExtToolkit', )
        self.container.setVisible(False)
        self.container.createPeer(toolkit, None)
        self.container.execute()

    def actionPerformed(self, actionEvent):
        try:
            url = self.url_entry.Text
            PLUGIN.set_server(url)
            self.accept()
        except:
            traceback.print_exc()

class SearchDialog(Dialog):

    TITLE = "Search"
    ACTION_NAME = "..."
    TYPE = "Document"
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
                       ("reference", self.name_entry),
                       ("revision", self.rev_entry),
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
        self.display_results(PLUGIN.get_data("api/search/?%s" % get)["objects"])

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
    ALL_FILES = True

    def do_action(self, doc, doc_file):
        PLUGIN.download(doc, doc_file)
        self.accept()

class CheckInDialog(Dialog):

    TITLE = "Check-in..."
    ACTION_NAME = "Check-in"
    WIDTH = 200
    HEIGHT = 100

    def __init__(self, ctx, doc, name):
        Dialog.__init__(self, ctx)
        self.doc = doc
        self.name = name

    def run(self):
        
        text = "%s|%s|%s" % (self.doc["reference"], self.doc["revision"],
                                       self.doc["type"])

        label = self.addWidget('label', 'FixedText', 5, 10, 60, 14,
                               Label = text)
        self.unlock_button = self.addWidget('unlock_button', 'CheckBox',
                                            5, 30, 100, 14, Label='Unlock ?')

        button = self.addWidget('action', 'Button', 55, 85, 50, 14,
                                Label=self.ACTION_NAME)
        self.container = smgr.createInstanceWithContext(
            'com.sun.star.awt.UnoControlDialog', )
        self.container.setModel(self.dialog)
        self.container.getControl('action').addActionListener(self)
        toolkit = smgr.createInstanceWithContext(
            'com.sun.star.awt.ExtToolkit', )
        self.container.setVisible(False)
        self.container.createPeer(toolkit, None)
        self.container.execute()

    def actionPerformed(self, actionEvent):
        try:
            doc = desktop.getCurrentComponent()
            unlock = self.get_value(self.unlock_button, None)
            PLUGIN.check_in(doc, unlock)
            self.accept()
        except:
            traceback.print_exc()

class ReviseDialog(Dialog):

    TITLE = "Revise..."
    ACTION_NAME = "Revise"
    WIDTH = 200
    HEIGHT = 100

    def __init__(self, ctx, doc, name, revision):
        Dialog.__init__(self, ctx)
        self.doc = doc
        self.name = name
        self.revision = revision
        self.gdoc = None

    def run(self):
        
        text = "%s|" % self.doc["reference"]
        label = self.addWidget('ref', 'FixedText', 5, 10, 60, 14,
                               Label = text)
        self.revision_entry = self.addWidget("rev_button", "Edit", 70, 10, 60, 14,
                                              Text=self.revision)
        text = "|%s" % self.doc["type"]
        label = self.addWidget('type', 'FixedText', 135, 10, 60, 14,
                               Label=text)
        self.unlock_button = self.addWidget('unlock_button', 'CheckBox',
                                            5, 30, 100, 14, Label='Unlock ?')

        button = self.addWidget('action', 'Button', 55, 85, 50, 14,
                                Label=self.ACTION_NAME)
        text = "Warning, old revision file will be automatically unlocked!"
        label = self.addWidget('warning', 'FixedText', 5, 45, 150, 14,
                               Label=text)
        self.container = smgr.createInstanceWithContext(
            'com.sun.star.awt.UnoControlDialog', )
        self.container.setModel(self.dialog)
        self.container.getControl('action').addActionListener(self)
        toolkit = smgr.createInstanceWithContext(
            'com.sun.star.awt.ExtToolkit', )
        self.container.setVisible(False)
        self.container.createPeer(toolkit, None)
        self.container.execute()

    def actionPerformed(self, actionEvent):
        try:
            self.accept()
            self.gdoc = PLUGIN.revise(desktop.getCurrentComponent(),
                          self.get_value(self.revision_entry, None),
                          self.get_value(self.unlock_button, None))
        except:
            traceback.print_exc()

class AttachToPartDialog(SearchDialog):
    TITLE = "Attach to part"
    ACTION_NAME = "Attach"
    TYPE = "Part"
    TYPES_URL = "api/parts/"
    EXPAND_FILES = False

    def __init__(self, ctx, doc):
        SearchDialog.__init__(self, ctx)
        self.doc = doc
    
    def do_action(self, part):
        PLUGIN.attach_to_part(self.doc, part["id"])
        self.accept()
    
    def actionPerformed(self, actionEvent):
        try:
            if actionEvent.Source == self.container.getControl('search_button'):
                self.search()
            elif actionEvent.Source == self.container.getControl('action_button'):
                node =  self.container.getControl('tree').getSelection()
                doc = self.nodes[node.getDisplayValue()]
                self.do_action(doc)
        except:
            traceback.print_exc()

class CreateDialog(SearchDialog):

    TITLE = "Create a document..."
    ACTION_NAME = "Create"
    TYPE = "Document"
    TYPES_URL = "api/docs/"

    WIDTH = 200
    HEIGHT = 200
    PAD = 5
    ROW_HEIGHT = 15
    ROW_PAD = 2

    def run(self):
        self.doc_created = False
        docs = PLUGIN.get_data(self.TYPES_URL)
        self.types = docs["types"]

        fields = [("type", 'ListBox'),
                 ]
        self.fields = []
        for i, (text, entry) in enumerate(fields): 
            x, y, w, h = self.get_position(i, 1)
            label = self.addWidget('%s_label' % text, 'FixedText', x, y, w, h,
                               Label = '%s:' % text.capitalize())
            x, y, w, h = self.get_position(i, 2)
            widget = self.addWidget('%s_entry' % text, entry, x, y, w, h)
            self.fields.append((text, widget))

        self.type_entry = self.fields[0][1]
        self.type_entry.StringItemList = tuple(self.types)
        self.type_entry.SelectedItems = (self.types.index(self.TYPE),)
        self.type_entry.Dropdown = True
        self.type_entry.MultiSelection = False
        
        self.advanced_fields = []
        self.display_fields(self.TYPE)
       
        row = len(self.fields) + len(self.advanced_fields)
        x, y, w, h = self.get_position(row, 1)
        self.filename_label = self.addWidget('filenameLabel', 'FixedText',
                                             x, y, w, h, Label="Filename")
        x, y, w, h = self.get_position(row, 2)
        self.filename_entry = self.addWidget('filename', 'Edit', x, y, w, h)
        x, y, w, h = self.get_position(row + 1, 1)
        self.unlock_button = self.addWidget('unlock', 'CheckBox', x, y, w, h,
                                Label="Unlock ?")
        x, y, w, h = self.get_position(row + 2, 2)
        self.action_button = self.addWidget('action_button', 'Button', x, y, w, h,
                                Label=self.ACTION_NAME)

        self.container = smgr.createInstanceWithContext(
            'com.sun.star.awt.UnoControlDialog', )
        self.container.setModel(self.dialog)
        self.container.getControl('action_button').addActionListener(self)
        self.container.getControl('type_entry').addItemListener(self)
        toolkit = smgr.createInstanceWithContext(
            'com.sun.star.awt.ExtToolkit', )
        self.container.setVisible(False)
        self.container.createPeer(toolkit, None)
        self.container.execute()

    def display_fields(self, typename):
        fields = PLUGIN.get_data("api/creation_fields/%s/" % typename)["fields"]
        temp = {}
        for field, entry in self.advanced_fields:
            name = field["name"]
            temp[name] = self.get_value(entry, field)
            self.container.getControl(entry.Name).setVisible(False)
            entry.dispose()
            self.dialog.removeByName(entry.Name)
            label = self.dialog.getByName("%s_label" % name)
            self.container.getControl(label.Name).setVisible(False)
            label.dispose()
            self.dialog.removeByName(label.Name)
        self.advanced_fields = []
        row = len(self.fields)
        for i, field in enumerate(fields):
            text, name = field["label"], field["name"]
            x, y, w, h = self.get_position(i + row, 1)
            label = self.addWidget('%s_label' % name, 'FixedText',
                                   x, y, w, h, Label='%s:' % text.capitalize())
            x, y, w, h = self.get_position(i + row, 2)
            widget = self.field_to_widget(field, x, y, w, h)
            if name in temp:
                self.set_value(widget, temp[name], field)
            self.advanced_fields.append((field, widget))
        if hasattr(self, 'container'):
            self.container.getPeer().invalidate(UPDATE|1)
            x, y, w, h = self.get_position(row + i + 1, 1)
            self.filename_label.PositionY = y
            self.filename_entry.PositionY = y
            x, y, w, h = self.get_position(row + i + 2, 1)
            self.unlock_button.PositionY = y
            x, y, w, h = self.get_position(row + i + 3, 1)
            self.action_button.PositionY = y

    def actionPerformed(self, actionEvent):
        try:
            if actionEvent.Source == self.container.getControl('action_button'):
                b, error = PLUGIN.create(self.get_creation_data(),
                              self.get_value(self.filename_entry, None),
                              self.get_value(self.unlock_button, None))
                if b:
                    self.accept()
                else:
                    show_error(error, self.container.getPeer())
                self.doc_created = b
        except:
            traceback.print_exc()

    def get_creation_data(self):
        data = {}
        for field_name, widget in self.fields:
            data[field_name] = self.get_value(widget, None)
        for field, widget in self.advanced_fields:
            data[field["name"]] = self.get_value(widget, field)
        return data

    def itemStateChanged(self, itemEvent):
        try:
            typename = self.types[self.type_entry.SelectedItems[0]]
            self.display_fields(typename)
        except:
            traceback.print_exc()


class OpenPLMLogin:

    def Activated(self):
        dialog = LoginDialog()
        dialog.exec_()

    def GetResources(self): 
        return {'Pixmap' : 'plop.png', 'MenuText': 'Login', 'ToolTip': 'Login'} 

FreeCADGui.addCommand('OpenPLM_Login', OpenPLMLogin())

class OpenPLMConfigure:

    def Activated(self):
        dialog = ConfigureDialog()
        dialog.run()

    def GetResources(self): 
        return {'Pixmap' : 'plop.png', 'MenuText': 'Configure', 'ToolTip': 'Configure'} 

FreeCADGui.addCommand('OpenPLM_Configure', OpenPLMConfigure())

class OpenPLMCheckOut:

    def Activated(self):
        dialog = CheckOutDialog()
        dialog.exec_()
    
    def GetResources(self): 
        return {'Pixmap' : 'plop.png', 'MenuText': 'Check-out', 'ToolTip': 'Check-out'} 

FreeCADGui.addCommand('OpenPLM_CheckOut', OpenPLMCheckOut())


class OpenPLMDownload:
    
    def Activated(self):
        dialog = DownloadDialog()
        dialog.run()

    def GetResources(self): 
        return {'Pixmap' : 'plop.png', 'MenuText': 'Download', 'ToolTip': 'Download'} 

FreeCADGui.addCommand('OpenPLM_Download', OpenPLMDownload())

class OpenPLMForget:

    def Activated(self):
        PLUGIN.forget(close_doc=True)

    def GetResources(self): 
        return {'Pixmap' : 'plop.png', 'MenuText': 'Forget current file',
                'ToolTip': 'Forget and delete current file'} 

FreeCADGui.addCommand('OpenPLM_Forget', OpenPLMForget())

class OpenPLMCheckIn:
    
    def Activated(self):
        gdoc = self.desktop.getCurrentComponent()
        if gdoc and gdoc in PLUGIN.documents:
            doc = PLUGIN.documents[gdoc]["openplm_doc"]
            doc_file_id = PLUGIN.documents[gdoc]["openplm_file_id"]
            path = PLUGIN.documents[gdoc]["openplm_path"]
            if not doc or not PLUGIN.check_is_locked(doc["id"], doc_file_id):
                return
            name = os.path.basename(path)
            dialog = CheckInDialog(doc, name)
            dialog.run() 
            if gdoc not in PLUGIN.documents:
                close(gdoc, self.desktop)
            else:
                win = gdoc.CurrentController.Frame.ContainerWindow
                show_error("Document not stored in OpenPLM", win)

    def GetResources(self): 
        return {'Pixmap' : 'plop.png', 'MenuText': 'Check-in', 'ToolTip': 'Check-in'} 

FreeCADGui.addCommand('OpenPLMCheckIn', OpenPLMCheckIn())

class OpenPLMRevise:

    def Activated(self):
        gdoc = self.desktop.getCurrentComponent()
        if gdoc and gdoc in PLUGIN.documents:
            doc = PLUGIN.documents[gdoc]["openplm_doc"]
            doc_file_id = PLUGIN.documents[gdoc]["openplm_file_id"]
            path = PLUGIN.documents[gdoc]["openplm_path"]
            if not doc or not PLUGIN.check_is_locked(doc["id"], doc_file_id):
                return
            revisable = PLUGIN.get_data("api/object/%s/isrevisable/" % doc["id"])["revisable"]
            if not revisable:
                win = gdoc.CurrentController.Frame.ContainerWindow
                show_error("Document can not be revised", win)
                return
            res = PLUGIN.get_data("api/object/%s/nextrevision/" % doc["id"])
            revision = res["revision"]
            name = os.path.basename(path)
            dialog = ReviseDialog(doc, name, revision)
            dialog.run()
            if gdoc not in PLUGIN.documents:
                close(gdoc, self.desktop)
                if dialog.gdoc and dialog.gdoc not in PLUGIN.documents:
                    close(dialog.gdoc, self.desktop)
                else:
                    win = gdoc.CurrentController.Frame.ContainerWindow
                    show_error("Document not stored in OpenPLM", win)

    def GetResources(self): 
        return {'Pixmap' : 'plop.png', 'MenuText': 'Revise', 'ToolTip': 'Revise'} 

FreeCADGui.addCommand('OpenPLM_Revise', OpenPLMRevise())

class OpenPLMAttach:

    def Activated(self):
        gdoc = self.desktop.getCurrentComponent()
        if gdoc and gdoc in PLUGIN.documents:
            doc = PLUGIN.documents[gdoc]["openplm_doc"]
            dialog = AttachToPartDialog(doc)
            dialog.run()
        else:
            win = gdoc.CurrentController.Frame.ContainerWindow
            show_error("Document not stored in OpenPLM", win)

    def GetResources(self): 
        return {'Pixmap' : 'plop.png', 'MenuText': 'Attach to a part',
                'ToolTip': 'Attach to a part'} 

FreeCADGui.addCommand('OpenPLM_Attach', OpenPLMAttach())

class OpenPLMCreate:
    
    def Activated(self):
        gdoc = self.desktop.getCurrentComponent()
        win = gdoc.CurrentController.Frame.ContainerWindow
        if not gdoc:
            show_error("Need an opened file to create a document", win)
            return
        if gdoc in PLUGIN.documents:
            show_error("Current file already attached to a document", win)
            return
        dialog = CreateDialog()
        resp = dialog.run()
        if dialog.doc_created and gdoc not in PLUGIN.documents:
            close(gdoc, self.desktop)

    def GetResources(self): 
        return {'Pixmap' : 'plop.png', 'MenuText': 'Create a Document',
                'ToolTip': 'Create a document'} 

FreeCADGui.addCommand('OpenPLM_Create', OpenPLMCreate())

def main_window():
    app = qt.qApp
    for x in app.topLevelWidgets():
        if type(x) == qt.QMainWindow:
            return x

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
