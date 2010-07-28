function Plugin(){
    this.username = "";
    this.password = "";
    this.SERVER =  "http://localhost:8000/"; 
    this.xrequest = Components.classes["@mozilla.org/xmlextras/xmlhttprequest;1"]
                            .createInstance(Components.interfaces.nsIXMLHttpRequest);

    // methods
    this.login = login;
    this.send_post = send_post;
    this.checkin = checkin;
    this.add_file = add_file;
    this.upload = upload;
}

function send_post(url, data) {
    var params = "";
    for (var key in data){
        params += key + "=" + data[key] + "&";
    }
    this.xrequest.open("POST", url, false);
    this.xrequest.send(params);
    var result = this.xrequest.responseText;
    return JSON.parse(result);
}

function login(username, password){
    var url = this.SERVER + "api/login/";
    var res = this.send_post(url, {"username" : username, "password" : password});
    return res;
}

function add_file(doc, path){
    var id = doc["id"];
    var url = this.SERVER + "api/object/" + id + "/add_file/";
    this.upload(url, path);
}

function checkin(doc){
    paths = save_messages();
    var obj = this;
    paths.forEach(function(path){
            obj.add_file(doc, path);
            });
}

function upload(url, filename) {
    // open the local file
    var file = Components.classes["@mozilla.org/file/local;1"]
        .createInstance(Components.interfaces.nsILocalFile);
    file.initWithPath( filename );      
   /* // Make a stream from a file.
    var stream = Components.classes["@mozilla.org/network/file-input-stream;1"]
        .createInstance(Components.interfaces.nsIFileInputStream);
    stream.init(file, 0x04 | 0x08, 0600, 0x04); // file is an nsIFile instance   

    // Try to determine the MIME type of the file
    var mimeType = "text/plain";
    try {
        var mimeService = Components.classes["@mozilla.org/mime;1"]
            .getService(Components.interfaces.nsIMIMEService);
        mimeType = mimeService.getTypeFromFile(file); // file is an nsIFile instance
    }
    catch(e) {  }

    */

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
    this.xrequest.setRequestHeader("Content-Type", "multipart/form-data; boundary=" + BOUNDARY);

    this.xrequest.send(mis);
    var result = this.xrequest.responseText;
    alert(result);
}


var PLUGIN = new Plugin();


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

function save_messages(){
    var nb = gFolderDisplay.selectedCount;
    var paths = new Array(nb);
    var messages = gFolderDisplay.selectedMessages;
    if (nb == 0){
        return paths;
    }
    for (var i = 0; i < nb; i++){
        var content = "";
        var folder =  messages[0].folder;
        var MessageURI = folder.getUriForMsg(messages[i]);
        var MsgService = messenger.messageServiceFromURI(MessageURI);
        var MsgStream = Components.classes["@mozilla.org/network/sync-stream-listener;1"].createInstance();
        var consumer = MsgStream.QueryInterface(Components.interfaces.nsIInputStream);
        var ScriptInput = Components.classes["@mozilla.org/scriptableinputstream;1"].createInstance();
        var ScriptInputStream = ScriptInput.QueryInterface(Components.interfaces.nsIScriptableInputStream);
        ScriptInputStream.init(consumer);
        var file = Components.classes["@mozilla.org/file/directory_service;1"].
            getService(Components.interfaces.nsIProperties).
            get("TmpD", Components.interfaces.nsIFile);
        file.append(GenerateFilenameFromMsgHdr(messages[i])+".eml");
        file.createUnique(Components.interfaces.nsIFile.NORMAL_FILE_TYPE, 0600);
        try {
            MsgService.streamMessage(MessageURI, MsgStream, msgWindow, null, false, null);
        } catch (ex) {
            alert("error: "+ex)
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

// interface
var openplm = {

onLoad: function() {
            // initialization code
            this.initialized = true;
        },

onOpenPLMLogin: function(e) {

                    var user = "user";
                    var pw = "pass";
                    while (true){
                        var prompts = Components.classes["@mozilla.org/embedcomp/prompt-service;1"]
                            .getService(Components.interfaces.nsIPromptService);
                        var username = {value: user};              // default the username to user
                        var password = {value: pw};              // default the password to pass
                        var check = {value: true};                   // default the checkbox to true
                        var result = prompts.promptUsernameAndPassword(null, "Title", "Enter username and password:",
                                username, password, null, check);

                        // result is true if OK was pressed, false if cancel was pressed. username.value,
                        // // password.value, and check.value are set if OK was pressed.
                        if (result == false){
                            return;
                        }
                        var res = PLUGIN.login(username.value, password.value);
                        if (res["result"] != "ok"){
                            user = username.value;
                            pw = password.value;
                            alert(res["error"]);
                        }else{
                            return;
                        }
                    }
                },

onOpenPLMCheckIn: function(e) {
                      PLUGIN.checkin({"id" : 30});
                  }

};

window.addEventListener("load", openplm.onLoad, false);
