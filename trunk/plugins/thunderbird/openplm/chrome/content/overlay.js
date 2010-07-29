Components.utils.import("resource://openplm/openplm.jsm");  

// interface
var openplm = {

onLoad: function() {
            // initialization code
            this.initialized = true;
        },

onOpenPLMLogin: function(e) {

                    OPENPLM.gFolderDisplay = gFolderDisplay;
                    OPENPLM.messenger = messenger;
                    var user = "";
                    var pw = "";
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
                            document.getElementById("openplm-checkin-menu-item").disabled = true;  
                            alert(res["error"]);
                        }else{
                            document.getElementById("openplm-checkin-menu-item").disabled = false;  
                            return;
                        }
                    }
                },

add_types: function(e){
               var docs = OPENPLM.get_docs();
               docs.forEach(function(x){
                       var e = document.getElementById('document-list').appendItem(x, x);
                       if (x == "Document"){
                       document.getElementById('document-list').selectedItem = e;
                       }
                       });
           },

search: function(e){
            var ref = document.getElementById("openplm-reference").value;
            var rev = document.getElementById("openplm-revision").value;
            var type = document.getElementById("document-list").value;

            var docs = OPENPLM.search({"reference" : ref, "revision": rev, "type" : type});
            var theList = document.getElementById('result-list');
            while (theList.getRowCount() > 0){
                theList.removeItemAt(0);
            }
            for (var i = 0; i < docs.length; i++)
            {
                var columns = ["type", "reference", "revision", "name",  "id"];
                var row = document.createElement('listitem');
                columns.forEach(
                        function(col){
                        var cell = document.createElement('listcell');
                        cell.setAttribute('label', docs[i][col]);
                        if (col == "id"){
                            cell.setAttribute('hidden', true);
                        }
                        row.appendChild(cell);
                        });
                row.setAttribute("value", docs[i]["id"]);

                theList.appendChild(row);
            }
                 document.documentElement.getButton("accept").disabled = true;  

        },

initCheckIn: function(e){
                 openplm.add_types();
                 document.documentElement.getButton("accept").disabled = true;  
             },

onCheckInSelectedItem: function(e){
                 var theList = document.getElementById('result-list');
                 var item = theList.selectedItem;
                 document.documentElement.getButton("accept").disabled = item == null;  
                
                       },

onOpenPLMCheckIn: function(e) {
                      let someValue = 2;
                      let params = {"out" : null  };

                      var win = window.openDialog(
                              "chrome://openplm/content/checkin.xul",
                              "openplm-checkin-dialog", "chrome,dialog,centerscreen,resizable=yes,modal",
                              params); // you can send as many extra parameters as you need.

                      if (params.out) {
                          var success = OPENPLM.checkin({"id" : params.out.id});
                          if (success){
                              alert("Mails have been successfully checked-in");
                          }
                      }
                  },

onCheckInOK: function(e){
                 // Return the changed arguments.
                 // Notice if user clicks cancel, window.arguments[0].out remains null
                 // because this function is never called
                 
                 var theList = document.getElementById('result-list');
                 var item = theList.selectedItem;
                 if (item){
                    window.arguments[0].out = {id : item.value};
                 }
                 return true;

             },

};

window.addEventListener("load", openplm.onLoad, false);
