var EXPORTED_SYMBOLS = ["OPENPLM"];

Components.utils.import("resource:///modules/activity/activityModules.js");
Components.utils.import("resource://gre/modules/PluralForm.jsm");
Components.utils.import("resource:///modules/attachmentChecker.js");

Components.utils.import("resource:///modules/MailUtils.js");
Components.utils.import("resource:///modules/errUtils.js");
var msgWindow = Components.classes["@mozilla.org/messenger/msgwindow;1"]
.createInstance(Components.interfaces.nsIMsgWindow);
var Application = Components.classes["@mozilla.org/steel/application;1"].getService(Components.interfaces.steelIApplication);
var prompts = Components.classes["@mozilla.org/embedcomp/prompt-service;1"]
.getService(Components.interfaces.nsIPromptService);


function Plugin(){
    this.username = "";
    this.password = "";
    var new_url = Application.prefs.getValue("extensions.openplm.server", "http://localhost:8000/"); 
    this.SERVER = new_url.replace(/([^\/])$/, "$1/");
    this.xrequest = Components.classes["@mozilla.org/xmlextras/xmlhttprequest;1"]
        .createInstance(Components.interfaces.nsIXMLHttpRequest);
    this.gFolderDisplay = null;
    this.messenger = null;

    // methods
    this.login = login;
    this.send_post = send_post;
    this.send_get = send_get;
    this.checkin = checkin;
    this.add_file = add_file;
    this.upload = upload;
    this.get_docs = get_docs;
    this.search = search;
    this.get_creation_fields = get_creation_fields;
    this.create = create;
}

function changeServer(e){
    var new_url = Application.prefs.getValue("extensions.openplm.server", "http://localhost:8000/"); 
    OPENPLM.SERVER = new_url.replace(/([^\/])$/, "$1/");
    if (OPENPLM.username != ""){
        try {
            OPENPLM.login(OPENPLM.username, OPENPLM.password);
        }catch (ex) {
        }    
    }
    return false;
}
Application.prefs.get("extensions.openplm.server").events.addListener("change", changeServer);


function send_post(url, data) {
    var params = "";
    for (var key in data){
        params += key + "=" + escape(data[key]) + "&";
    }
    this.xrequest.open("POST", url, false);
    this.xrequest.setRequestHeader('User-Agent', 'openplm');
    var result;
    try {
        this.xrequest.send(params);
        var result_json = this.xrequest.responseText;
        result = JSON.parse(result_json);
    }catch (er){
        throw "can not open " + url;
    }
    if (result["result"] != "ok"){
        throw result["error"];
    }
    return result;
}

function send_get(url, data) {
    var params = "";
    for (var key in data){
        params += key + "=" + escape(data[key]) + "&";
    }
    this.xrequest.open("GET", url + "?"+params, false);
    this.xrequest.setRequestHeader('User-Agent', 'openplm');
    var result;
    try {
        this.xrequest.send();
        var result_json = this.xrequest.responseText;
        result = JSON.parse(result_json);
    }catch (er){
        throw "can not open " + url;
    }

    if (result["result"] != "ok"){
        throw result["error"];
    }
    return result;
}

function search(query){
    var url = this.SERVER + "api/search/true/false/";
    return this.send_get(url, query)["objects"];
}

function get_docs(){
    var url = this.SERVER + "api/docs/";
    return this.send_get(url, {})["types"];
}

function get_creation_fields(type){
    var url = this.SERVER + "api/creation_fields/" + type + "/";
    return this.send_get(url, {})["fields"];
}



function login(username, password){
    var url = this.SERVER + "api/login/";
    var res = this.send_post(url, {"username" : username, "password" : password});
    this.username = username;
    this.password = password;
    return res;
}

function add_file(doc, path){
    var id = doc["id"];
    var url = this.SERVER + "api/object/" + id + "/add_file/";
    var result = JSON.parse(this.upload(url, path));
    return result["result"];
}

function checkin(doc){
    var paths = save_messages();
    var obj = this;
    var success = true;
    paths.forEach(function(path){
            success = success && (obj.add_file(doc, path) == "ok");
            });
    return success;
}

function upload(url, filename) {
    // open the local file
    var file = Components.classes["@mozilla.org/file/local;1"]
        .createInstance(Components.interfaces.nsILocalFile);
    file.initWithPath( filename );      

    const BOUNDARY = "111222111"; //ce qui va nous servir de délimiteur
    const MULTI    = "@mozilla.org/io/multiplex-input-stream;1";
    const FINPUT   = "@mozilla.org/network/file-input-stream;1";
    const STRINGIS = "@mozilla.org/io/string-input-stream;1";
    const BUFFERED = "@mozilla.org/network/buffered-input-stream;1";
    const nsIMultiplexInputStream = Components.interfaces.nsIMultiplexInputStream;
    const nsIFileInputStream      = Components.interfaces.nsIFileInputStream;
    const nsIStringInputStream    = Components.interfaces.nsIStringInputStream;
    const nsIBufferedInputStream  = Components.interfaces.nsIBufferedInputStream;

    var mis = Components.classes[MULTI].createInstance(nsIMultiplexInputStream);
    var fin = Components.classes[FINPUT].createInstance(nsIFileInputStream);
    fin.init(file, 0x01, 0444, null); //fic est un objet de type fichier
    var buf = Components.classes[BUFFERED].createInstance(nsIBufferedInputStream);
    buf.init(fin, 4096);
    var hsis = Components.classes[STRINGIS].createInstance(nsIStringInputStream);
    var sheader = new String();
    sheader += "--" + BOUNDARY + "\r\nContent-disposition: form-data;name=\"addfile\"\r\n\r\n1";
    sheader += "\r\n" + "--" + BOUNDARY + "\r\n";
    sheader += "Content-disposition: form-data;name=\"filename\";filename=\"" + file.leafName + "\"\r\n";
    sheader += "Content-Type: application/octet-stream\r\n";
    sheader += "Content-Length: " + file.fileSize+"\r\n\r\n";
    var converter = Components.classes["@mozilla.org/intl/scriptableunicodeconverter"]
        .createInstance(Components.interfaces.nsIScriptableUnicodeConverter);

    converter.charset = "UTF-8";
    sheader = converter.ConvertFromUnicode(sheader);

    hsis.setData(sheader, sheader.length);

    var endsis = Components.classes[STRINGIS].createInstance(nsIStringInputStream);
    var bs = new String("\r\n--" + BOUNDARY + "--\r\n");
    endsis.setData(bs, bs.length);

    mis.appendStream(hsis);
    mis.appendStream(buf);
    mis.appendStream(endsis);
    // Send
    this.xrequest.open('POST', url, false); /* synchronous! */
    this.xrequest.setRequestHeader("Content-Length", mis.available());
    this.xrequest.setRequestHeader('User-Agent', 'openplm');
    this.xrequest.setRequestHeader("Content-Type", "multipart/form-data; boundary=" + BOUNDARY);

    this.xrequest.send(mis);
    var result = this.xrequest.responseText;
    return result;
}

function create(data){
    var url = this.SERVER + "api/create/";
    var doc = this.send_post(url, data)["object"];
    return this.checkin(doc);
}

// utilities
function GenerateFilenameFromMsgHdr(msgHdr) {

    function MakeIS8601ODateString(date) {
        function pad(n) {return n < 10 ? "0" + n : n;}
        return date.getFullYear() + "-" +
            pad(date.getMonth() + 1)  + "-" +
            pad(date.getDate())  + " " +
            pad(date.getHours())  + "" +
            pad(date.getMinutes()) + "";
    }

    let filename;
    if (msgHdr.flags & Components.interfaces.nsMsgMessageFlags.HasRe)
        filename = (msgHdr.mime2DecodedSubject) ? "Re: " + msgHdr.mime2DecodedSubject : "Re: ";
    else
        filename = msgHdr.mime2DecodedSubject;

    filename += " - ";
    filename += msgHdr.mime2DecodedAuthor  + " - ";
    filename += MakeIS8601ODateString(new Date(msgHdr.date/1000));

    return filename;

}
function GenerateValidFilename(filename, extension)
{
  if (filename) // we have a title; let's see if it's usable
  {
    // clean up the filename to make it usable and
    // then trim whitespace from beginning and end
    filename = validateFileName(filename).trim();
    if (filename.length > 0)
      return filename + extension;
  }
  return null;
}

function validateFileName(aFileName)
{
    var re = /[\/]+/g;
    aFileName = aFileName.replace(re, "_");

    re = /[\\\/\|]+/g;
    aFileName.replace(re, "_");
    aFileName = aFileName.replace(/[\"]+/g, "_");
    aFileName = aFileName.replace(/[\*\:\?]+/g, " ");
    aFileName = aFileName.replace(/[\<]+/g, " ");
    aFileName = aFileName.replace(/[\>]+/g, " ");
    re = /[\:\/]+/g;
  
  return aFileName.replace(re, "_");
}
function save_messages(){
    var nb = OPENPLM.gFolderDisplay.selectedCount;
    var paths = new Array(nb);
    var messages = OPENPLM.gFolderDisplay.selectedMessages;
    if (nb == 0){
        return paths;
    }
    for (var i = 0; i < nb; i++){
        var content = "";
        var folder =  messages[0].folder;
        var MessageURI = folder.getUriForMsg(messages[i]);
        var MsgService = OPENPLM.messenger.messageServiceFromURI(MessageURI);
        var MsgStream = Components.classes["@mozilla.org/network/sync-stream-listener;1"].createInstance();
        var consumer = MsgStream.QueryInterface(Components.interfaces.nsIInputStream);
        var ScriptInput = Components.classes["@mozilla.org/scriptableinputstream;1"].createInstance();
        var ScriptInputStream = ScriptInput.QueryInterface(Components.interfaces.nsIScriptableInputStream);
        ScriptInputStream.init(consumer);
        var file = Components.classes["@mozilla.org/file/directory_service;1"].
            getService(Components.interfaces.nsIProperties).
            get("TmpD", Components.interfaces.nsIFile);
        file.append(GenerateValidFilename(GenerateFilenameFromMsgHdr(messages[i]), ".eml"));
        file.createUnique(Components.interfaces.nsIFile.NORMAL_FILE_TYPE, 0600);
        try {
            MsgService.streamMessage(MessageURI, MsgStream, msgWindow, null, false, null);
        } catch (ex) {
            dump("error: "+ex);
        }
        ScriptInputStream.available();
        var foStream = Components.classes["@mozilla.org/network/file-output-stream;1"].  
            createInstance(Components.interfaces.nsIFileOutputStream);  

        // use 0x02 | 0x10 to open file for appending. 
        foStream.init(file, 0x02 | 0x08 | 0x20, 0600, 0);
        var converter = Components.classes["@mozilla.org/intl/converter-output-stream;1"].
            createInstance(Components.interfaces.nsIConverterOutputStream);
        converter.init(foStream, "UTF-8", 0, 0);
        while (ScriptInputStream.available()) {
            converter.writeString( ScriptInputStream .read(512));
        }
        converter.close(); // this closes foStream
        paths[i] = file.path;
    }
    return paths;

}

var OPENPLM = new Plugin();

