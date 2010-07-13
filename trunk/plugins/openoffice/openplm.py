import os
import shutil
import json
import urllib

# poster makes it possible to send http request with files
# sudo easy_install poster
from poster.encode import multipart_encode
from poster.streaminghttp import StreamingHTTPRedirectHandler, StreamingHTTPHandler

import urllib2

import traceback
import uno
import unohelper

from com.sun.star.task import XJobExecutor
from com.sun.star.awt import XActionListener, XItemListener
from com.sun.star.awt.InvalidateStyle import CHILDREN, UPDATE
from com.sun.star.awt.tree import XTreeExpansionListener
from com.sun.star.view import XSelectionChangeListener
from com.sun.star.view.SelectionType import SINGLE


class OpenPLMPluginInstance(object):
    
    #: location of openPLM server
    SERVER = "http://localhost:8000/"
    #: OpenPLM main directory
    OPENPLM_DIR = os.path.expanduser("~/.openplm")
    #: directory where files are stored
    PLUGIN_DIR = os.path.join(OPENPLM_DIR, "openoffice")
    #: gedit plugin configuration file
    CONF_FILE = os.path.join(PLUGIN_DIR, "conf.json")

    def __init__(self):
        
        self.opener = urllib2.build_opener(StreamingHTTPHandler(),
                                           StreamingHTTPRedirectHandler(),
                                           urllib2.HTTPCookieProcessor())
        self.username = ""

        try:
            os.makedirs(self.OPENPLM_DIR, 0700)
        except os.error:
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
        else:
            raise ValueError()

    def check_out_cb(self):
        diag = CheckOutDialog(self._window, self)
        diag.run()
        diag.destroy()
    
    def download_cb(self):
        diag = DownloadDialog(self._window, self)
        diag.run()
        diag.destroy()
        
    def attach_cb(self):
        gdoc = self._window.get_active_document()
        doc = gdoc.get_data("openplm_doc")
        if not doc:
            return
        diag = AttachToPartDialog(self._window, self)
        diag.doc = doc
        diag.run()
        diag.destroy()

    def create_cb(self):
        gdoc = self._window.get_active_document()
        if not gdoc:
            show_error(_("Need an opened file to create a document"))
            return
        if gdoc.get_data("openplm_doc"):
            show_error(_("Current file already attached to a document"))
            return
        def func():
            diag = CreateDialog(self._window, self)
            def response_cb(diag, resp):
                if resp == gtk.RESPONSE_ACCEPT:
                    data = diag.get_creation_data()
                    res = self.get_data("api/create/", data)
                    if res["result"] != "ok":
                        # TODO
                        return
                    else:
                        doc = res["object"]
                        unlock = diag.get_unlock()
                        diag.destroy()
                        # create a new doc
                        rep = os.path.join(self.PLUGIN_DIR, doc["type"], doc["reference"],
                                           doc["revision"])
                        try:
                            os.makedirs(rep, 0700)
                        except os.error:
                            # directory already exists, just ignores the exception
                            pass
                        filename = os.path.basename(gdoc.get_uri())
                        path = os.path.join(rep, filename)
                        gdoc.set_uri("file://" + path)
                        def f():
                            doc_file = self.upload_file(doc, path)
                            self.add_managed_file(doc, doc_file, path)
                            self.load_file(doc, doc_file["id"], path)
                            if not unlock:
                                self.get_data("api/object/%s/lock/%s/" % (doc["id"], doc_file["id"]))
                        save_document(self._window, gdoc, f)
                else:
                    diag.destroy()
            diag.connect("response", response_cb)
            diag.show()
        save_document(self._window, gdoc, func)
    
    def get_data(self, url, data=None):
        data_enc = urllib.urlencode(data) if data else None
        return json.load(self.opener.open(self.SERVER + url, data_enc)) 

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
        self.get_data("api/object/%s/attach_to_part/%s/" % (doc["id"], part_id))

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

    def get_managed_files(self):
        data = self.get_conf_data()
        files = []
        for doc in data.get("documents", {}).itervalues():
            files.extend((d, doc) for d in doc.get("files", {}).items())
        return files
   
    def forget(self, gdoc=None, delete=True):
        gdoc = gdoc or self._window.get_active_document()
        doc = gdoc.get_data("openplm_doc")
        doc_file_id = gdoc.get_data("openplm_file_id")
        path = gdoc.get_data("openplm_path")
        if doc and doc_file_id and path:
            label = gdoc.get_data("openplm_label")
            label.destroy()
            data = self.get_conf_data()
            del data["documents"][str(doc["id"])]["files"][str(doc_file_id)]
            if not  data["documents"][str(doc["id"])]["files"]:
                del data["documents"][str(doc["id"])]
            f = open(self.CONF_FILE, "w")
            json.dump(data, f)
            f.close()
            if delete and os.path.exists(path):
                os.remove(path)

    def load_managed_files(self):
        for (doc_file_id, path), doc in self.get_managed_files():
            self.load_file(doc, doc_file_id, path)

    def load_file(self, doc, doc_file_id, path):
        document = desktop.loadComponentFromURL("file://" + path ,"_blank", 0, ()) 
        gdoc.set_data("openplm_doc", doc)
        gdoc.set_data("openplm_file_id", doc_file_id)
        gdoc.set_data("openplm_path", path)
        return gdoc

    def check_in(self, gdoc, unlock, save=True):
        doc = gdoc.get_data("openplm_doc")
        doc_file_id = gdoc.get_data("openplm_file_id")
        path = gdoc.get_data("openplm_path")
        if doc and doc_file_id and path:
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
            if save:
                save_document(self._window, gdoc, func)
            else:
                func()
        else:
            # TODO
            print 'can not check in'
            pass

    def check_in_cb(self):
        gdoc = self._window.get_active_document()
        doc = gdoc.get_data("openplm_doc")
        doc_file_id = gdoc.get_data("openplm_file_id")
        if not doc or not self.check_is_locked(doc["id"], doc_file_id):
            return
        name = os.path.basename(gdoc.get_data("openplm_path"))
        diag = CheckInDialog(self._window, self, doc, name)
        resp = diag.run()
        if resp == gtk.RESPONSE_ACCEPT:
            self.check_in(gdoc, diag.get_unlock())
        diag.destroy()
    
    def revise(self, gdoc, revision, unlock):
        doc = gdoc.get_data("openplm_doc")
        doc_file_id = gdoc.get_data("openplm_file_id")
        path = gdoc.get_data("openplm_path")
        if doc and doc_file_id and path:
          
            res = self.get_data("api/object/%s/revise/" % doc["id"],
                                {"revision" : revision})
            new_doc = res["doc"]
            name = os.path.basename(gdoc.get_uri())
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

            self.forget(gdoc)
            path = os.path.join(rep, name)
            gdoc.set_uri("file://" + path)
            def func():
                gd = self.load_file(new_doc, doc_file["id"], path)
                self.add_managed_file(new_doc, doc_file, path)
                self.check_in(gd, unlock, False)
                self.get_data("api/object/%s/unlock/%s/" % (doc["id"], doc_file_id))
            save_document(self._window, gdoc, func)
        else:
            # TODO
            print 'can not revise'

    def revise_cb(self):
        gdoc = self._window.get_active_document()
        doc = gdoc.get_data("openplm_doc")
        doc_file_id = gdoc.get_data("openplm_file_id")
        if not doc or not self.check_is_locked(doc["id"], doc_file_id):
            return
        revisable = self.get_data("api/object/%s/isrevisable/" % doc["id"])["revisable"]
        if not revisable:
            show_error(_("Document can not be revised"), self._window)
            return
        name = os.path.basename(gdoc.get_data("openplm_path"))
        doc_file_id = gdoc.get_data("openplm_file_id")
        res = self.get_data("api/object/%s/nextrevision/" % doc["id"])
        revision = res["revision"]
        diag = ReviseDialog(self._window, self, doc, name, revision)
        resp = diag.run()
        if resp == gtk.RESPONSE_ACCEPT:
            self.revise(gdoc, diag.get_revision(), diag.get_unlock())
        diag.destroy()

    def check_is_locked(self, doc_id, file_id, error_dialog=True):
        """
        Return True if file which is is *file_id* is locked.

        If it is unlocked and *error_dialog* is True, an ErrorDialog is 
        displayed
        """
        locked = self.get_data("api/object/%s/islocked/%s/" % (doc_id, file_id))["locked"]
        if not locked and error_dialog:
            show_error(_("File is not locked, action not allowed"), self._window)
        return locked


PLUGIN = OpenPLMPluginInstance()
def show_error(message, parent=None):
    print message

class Dialog(unohelper.Base, XActionListener):
    def __init__(self, ctx):
        self.ctx = ctx
        self.msg = None

    def addWidget(self, name, type, x, y, w, h, **kwargs):
        if "." in type:
            widget = self.dialog.createInstance('com.sun.star.awt.%s' % type)
        else:
            widget = self.dialog.createInstance('com.sun.star.awt.UnoControl%sModel' % type)
        widget.Name = name
        widget.PositionX = int(x)
        widget.PositionY = int(y)
        widget.Width = int(w)
        widget.Height = int(h)
        for k, w in kwargs.items():
            setattr(widget, k, w)
        self.dialog.insertByName(name, widget)
        return widget
    

    def get_value(self, entry, field):
        value = None
        if hasattr(entry, "Text"):
            value = entry.Text
        elif hasattr(entry, 'SelectedItems'):
            if not field:
                value = entry.StringItemList[entry.SelectedItems[0]]
            else:
                value = field["choices"][entry.SelectedItems[0]][0]
        elif hasattr(entry, "State"):
            value = bool(entry.State)
        return value

    def set_value(self, entry, value, field=None):
        if hasattr(entry, "Text"):
            entry.Text = value or ''
        elif hasattr(entry, 'SelectedItems'):
            choices = [c[0] for c in field["choices"]]
            entry.SelectedItems = (choices.index(value or ''), )
        elif hasattr(entry, "State"):
            entry.State = int(value or 0)
    
    def field_to_widget(self, field, x, y, w, h):
        type = ""
        attributes = {}
        if field["type"] in ("text", "int", "decimal", "float"):
            type = "Edit"
        elif field["type"] == "boolean":
            type = "CheckBox"
        elif field["type"] == "choice":
            type = "ListBox"
            choices = field["choices"]
            if [u'', u'---------'] not in choices:
                choices = ([u'', u'---------'],) + tuple(choices)
            field["choices"] = choices
            values = []
            for _, c in choices:
                values.append(c)
            attributes['StringItemList'] = tuple(values)
            attributes['Dropdown'] = True
            attributes['MultiSelection'] = False
        if type == "":
            raise ValueError()
        widget = self.addWidget("%s_entry" % field["name"], type, x, y, w, h,
                                **attributes) 
        self.set_value(widget, field["initial"], field)
        return widget


    def run(self):
        pass

    def actionPerformed(self, actionEvent):
        pass

class LoginDialog(Dialog):

    def run(self):
        smgr = self.ctx.ServiceManager
        self.dialog = smgr.createInstanceWithContext(
            'com.sun.star.awt.UnoControlDialogModel', self.ctx)
        self.dialog.Width = 200
        self.dialog.Height = 105
        self.dialog.Title = 'Login'
        label = self.addWidget('Username', 'FixedText', 5, 10, 100, 14,
                               Label = 'Username:')
        self.username = self.addWidget('UsernameEntry', 'Edit', 90, 10, 100, 14)
        label = self.addWidget('password', 'FixedText', 5, 30, 100, 14,
                               Label = 'Password:')
        self.password = self.addWidget('PasswordEntry', 'Edit', 90, 30, 100, 14,
                                       EchoChar=ord('*'))

        button = self.addWidget('login', 'Button', 55, 85, 50, 14,
                                Label = 'Login')
        self.container = smgr.createInstanceWithContext(
            'com.sun.star.awt.UnoControlDialog', self.ctx)
        self.container.setModel(self.dialog)
        self.container.getControl('login').addActionListener(self)
        toolkit = smgr.createInstanceWithContext(
            'com.sun.star.awt.ExtToolkit', self.ctx)
        self.container.setVisible(False)
        self.container.createPeer(toolkit, None)
        self.container.execute()

    def actionPerformed(self, actionEvent):
        try:
            username = self.username.Text
            password = self.password.Text
            try:
                PLUGIN.login(username, password)
                self.container.endExecute()
            except ValueError, e:
                print e
        except:
            traceback.print_exc()

class SearchDialog(Dialog, XItemListener,
                   XTreeExpansionListener, XSelectionChangeListener):

    TITLE = "Search"
    ACTION_NAME = "..."
    TYPE = "Document"
    TYPES_URL = "api/docs/"
    ALL_FILES = False

    WIDTH = 200
    HEIGHT = 300
    PAD = 5
    ROW_HEIGHT = 15
    ROW_PAD = 2


    def get_position(self, row, column):
        if column == 1:
            x = self.PAD
            w = (self.WIDTH - 3 * self.PAD) / 3
        else:
            x = self.PAD * 2 + (self.WIDTH-3*self.PAD) *1/3
            w = (self.WIDTH - 3 * self.PAD) * 2 / 3
        y = self.PAD + (self.ROW_HEIGHT + self.ROW_PAD) * row
        return x, y, w, self.ROW_HEIGHT

    def run(self):
        
        docs = PLUGIN.get_data(self.TYPES_URL)
        self.types = docs["types"]

        smgr = self.ctx.ServiceManager
        self.dialog = smgr.createInstanceWithContext(
            'com.sun.star.awt.UnoControlDialogModel', self.ctx)
        self.dialog.Width = self.WIDTH
        self.dialog.Height = self.HEIGHT
        self.dialog.Title = self.TITLE
        
        fields = [("type", 'ListBox'),
                  ("reference", 'Edit'),
                  ("revision", 'Edit'),
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
        
        x, y, w, h = self.get_position(len(self.fields)+len(self.advanced_fields)+1, 2)
        self.search_button = self.addWidget('search_button', 'Button', x, y, w, h,
                                Label = 'Search')
        
        self.tree = self.addWidget('tree', 'tree.TreeControlModel', 
                                   self.PAD, y + h +5, self.WIDTH-2*self.PAD, self.HEIGHT- (y+  2*h + 20))

        self.tree_model = self.createService("com.sun.star.awt.tree.MutableTreeDataModel")
        self.tree_root = self.tree_model.createNode("Results", True)
        self.tree_model.setRoot(self.tree_root)
        self.tree.DataModel = self.tree_model
        self.tree.SelectionType = SINGLE
        
        y = self.HEIGHT - self.PAD - h
        self.action_button = self.addWidget('action_button', 'Button', x, y, w, h,
                                Label = self.ACTION_NAME)
        #self.tree.addSelectionChangeListener(self)

        self.container = smgr.createInstanceWithContext(
            'com.sun.star.awt.UnoControlDialog', self.ctx)
        self.container.setModel(self.dialog)
        self.container.getControl('search_button').addActionListener(self)
        self.container.getControl('action_button').addActionListener(self)
        self.container.getControl('type_entry').addItemListener(self)
        self.container.getControl('tree').addTreeExpansionListener(self)
        toolkit = smgr.createInstanceWithContext(
            'com.sun.star.awt.ExtToolkit', self.ctx)
        self.container.setVisible(False)
        self.container.createPeer(toolkit, None)
        self.container.execute()

    def createService(self, cClass):
        return self.ctx.ServiceManager.createInstanceWithContext(cClass, self.ctx)


    def display_fields(self, typename):
        fields = PLUGIN.get_data("api/search_fields/%s/" % typename)["fields"]
        temp = {}
        for field, entry in self.advanced_fields:
            temp[field["name"]] = self.get_value(entry, field)
            entry.PositionX = -1000
            entry.PositionY = -1000
            entry.dispose()
            self.dialog.removeByName(entry.Name)
            label = self.dialog.getByName("%s_label" % field["name"])
            label.dispose()
            label.PositionX = -1000
            label.PositionY = -1000
            self.dialog.removeByName("%s_label" % field["name"])
        self.advanced_fields = []
        j = len(self.fields)
        for i, field in enumerate(fields):
            text = field["label"]
            x, y, w, h = self.get_position(i + j, 1)
            label = self.addWidget('%s_label' % field["name"], 'FixedText',
                                   x, y, w, h,
                                   Label = '%s:' % text.capitalize())
            x, y, w, h = self.get_position(i + j, 2)
            widget = self.field_to_widget(field, x, y, w, h)
            if field["name"] in temp:
                self.set_value(widget, temp[field["name"]], field)
            self.advanced_fields.append((field, widget))
        if hasattr(self, 'container'):
            self.container.getPeer().invalidate(UPDATE|1)
            #self.container.setVisible(True)
            x, y, w, h = self.get_position(len(self.fields)+len(self.advanced_fields)+1, 2)
            self.search_button.PositionX = x
            self.search_button.PositionY = y
            pos = self.tree.PositionY
            self.tree.PositionY = y + h + 5
            self.tree.Height -= self.tree.PositionY - pos

    def actionPerformed(self, actionEvent):
        try:
            if actionEvent.Source == self.container.getControl('search_button'):
                self.search()
            elif actionEvent.Source == self.container.getControl('action_button'):
                node =  self.container.getControl('tree').getSelection()
                doc = self.nodes[node.getParent().getDisplayValue()]
                doc_file = doc["files"][node.getParent().getIndex(node)]
                self.do_action(doc, doc_file)
        except:
            traceback.print_exc()

    def itemStateChanged(self, itemEvent):
        try:
            typename = self.types[self.type_entry.SelectedItems[0]]
            self.display_fields(typename)
        except:
            traceback.print_exc()

    def requestChildNodes(self, event):
        res = self.nodes[event.Node.getDisplayValue()]
        suffix = "all/" if self.ALL_FILES else ""
        url = "api/object/%s/files/%s" % (res["id"], suffix)
        files = PLUGIN.get_data(url)["files"]
        res["files"] = files
        for f in files:
            node = self.tree_model.createNode(f["filename"], False)
            event.Node.appendChild(node)
        self.container.getPeer().invalidate(UPDATE|1)

    def display_results(self, results):
        self.nodes = {}
        while self.tree_root.getChildCount():
            self.tree_root.removeChildByIndex(0)
        for res in results:
            text = "%(reference)s|%(type)s|%(revision)s" % res
            node = self.tree_model.createNode(text, True)
            self.tree_root.appendChild(node)
            self.nodes[node.getDisplayValue()] = res
        self.container.getPeer().invalidate(UPDATE|1)

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
        self.container.endExecute()

class OpenPLMLogin(unohelper.Base, XJobExecutor):
    def __init__(self, ctx):
        self.ctx = ctx

    def trigger(self, args):
        try:
            desktop = self.ctx.ServiceManager.createInstanceWithContext(
                'com.sun.star.frame.Desktop', self.ctx)
            dialog = LoginDialog(self.ctx)
            dialog.run()
        except:
            traceback.print_exc()


class OpenPLMCheckOut(unohelper.Base, XJobExecutor):
    def __init__(self, ctx):
        self.ctx = ctx

    def trigger(self, args):
        try:
            desktop = self.ctx.ServiceManager.createInstanceWithContext(
                'com.sun.star.frame.Desktop', self.ctx)
            dialog = CheckOutDialog(self.ctx)
            dialog.run()
            #doc = desktop.getCurrentComponent()
            #cursor = doc.getCurrentController().getViewCursor()
            #doc.Text.insertString(cursor, 'Hello World', 0)
        except:
            traceback.print_exc()

g_ImplementationHelper = unohelper.ImplementationHelper()

for cls in (OpenPLMLogin, OpenPLMCheckOut):
    g_ImplementationHelper.addImplementation(cls,
                                         'org.example.%s' % cls.__name__,
                                         ('com.sun.star.task.Job',))

