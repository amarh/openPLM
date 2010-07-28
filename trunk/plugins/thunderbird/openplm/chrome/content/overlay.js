Components.utils.import("resource://openplm/openplm.jsm");  

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
                        var res = OPENPLM.login(username.value, password.value);
                        if (res["result"] != "ok"){
                            user = username.value;
                            pw = password.value;
                            alert(res["error"]);
                        }else{
                            return;
                        }
                    }
                },

add_types: function(e){
               document.getElementById('document-list').appendItem("PLOPP");
           },

onOpenPLMCheckIn: function(e) {
                      let someValue = 2;
                      let returnValue = { accepted : false , result : "" };

                      window.openDialog(
                                "chrome://openplm/content/checkin.xul",
                                  "openplm-checkin-dialog", "chrome,centerscreen",
                                    someValue, returnValue); // you can send as many extra parameters as you need.
                      OPENPLM.checkin({"id" : 30});
                  }

};

window.addEventListener("load", openplm.onLoad, false);
