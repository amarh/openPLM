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
                        var result = prompts.promptUsernameAndPassword(null, "Login", "Enter username and password:",
                                username, password, null, check);

                        // result is true if OK was pressed, false if cancel was pressed. username.value,
                        // // password.value, and check.value are set if OK was pressed.
                        if (result == false){
                            return;
                        }
                        try{
                            var res = OPENPLM.login(username.value, password.value);
                            document.getElementById("openplm-checkin-menu-item").disabled = false;  
                            document.getElementById("openplm-create-menu-item").disabled = false;  
                            return;
                        }catch (er){
                            user = username.value;
                            pw = password.value;
                            document.getElementById("openplm-checkin-menu-item").disabled = true;  
                            document.getElementById("openplm-create-menu-item").disabled = true;  
                            alert(er);
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
            try {
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
            } catch (er){
                alert("Error :" + er);
            }
            document.documentElement.getButton("accept").disabled = true;  

        },

initCheckIn: function(e){
                 openplm.add_types();
                 document.documentElement.getButton("accept").disabled = true;  
             },

initCreate: function(e){
                openplm.add_types();
            },

onCheckInSelectedItem: function(e){
                           var theList = document.getElementById('result-list');
                           var item = theList.selectedItem;
                           document.documentElement.getButton("accept").disabled = item == null;  

                       },

onOpenPLMCheckIn: function(e) {
                      let params = {"out" : null  };

                      var win = window.openDialog(
                              "chrome://openplm/content/checkin.xul",
                              "openplm-checkin-dialog", "chrome,dialog,centerscreen,resizable=yes,modal",
                              params); 

                      if (params.out) {
                          try {
                              var success = OPENPLM.checkin({"id" : params.out.id});
                              if (success){
                                  alert("Mails have been successfully checked-in");
                              }
                          }catch (er){
                              alert("Error :" + er);
                          }
                      } 
                  },

onOpenPLMCreate: function(e) {
                     let params = {"out" : null  };

                     var win = window.openDialog(
                             "chrome://openplm/content/create.xul",
                             "openplm-create-dialog", "chrome,dialog,centerscreen,resizable=yes,modal",
                             params); 

                     if (params.out) {
                         try {
                             var success = OPENPLM.create(params.out);
                             if (success){
                                 alert("Document has been successfully created");
                             }
                         }catch (er){
                             alert("Error : " + er);
                         }


                     }
                 },

onCreateTypeChange: function(e){
                        const XUL_NS = "http://www.mozilla.org/keymaster/gatekeeper/there.is.only.xul";
                        var theList = document.getElementById('document-list');
                        var rows = document.getElementById('fields-list');
                        var type = theList.selectedItem.value;
                        try {
                            var fields = OPENPLM.get_creation_fields(type);
                        } catch (er){
                            alert("Error :" + er);
                        }
                        var temp = {}; 
                        while (rows.childElementCount > 1){
                            var child = rows.lastChild.lastChild;
                            var value = openplm.getWidgetValue(child);
                            temp[child.getUserData("field")["name"]] = value;
                            rows.removeChild(rows.lastChild);
                        }
                        fields.forEach(function(field){
                                var row = document.createElementNS(XUL_NS, 'row');

                                rows.appendChild(row);
                                var label = document.createElementNS(XUL_NS, "label");
                                label.setAttribute("value", field["label"]);
                                row.appendChild(label);
                                var widget = openplm.createWidget(field);
                                row.appendChild(widget);
                                if (field["name"] in temp){
                                openplm.setWidgetValue(widget, temp[field["name"]]);
                                }

                                });

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

onCreateOK: function(e){
                var data = {};
                var theList = document.getElementById('document-list');
                var rows = document.getElementById('fields-list');
                var type = theList.selectedItem.value;
                data["type"] = type;
                for (i=1; i < rows.childElementCount; i++){
                    var child = rows.children[i].lastChild;
                    var value = openplm.getWidgetValue(child);
                    data[child.getUserData("field")["name"]] = value;
                }
                window.arguments[0].out = data;
                return true;

            },

createWidget: function(field){
                  var convert = {"int" : "textbox",
                      "decimal" : "textbox",
                      "float" : "textbox",
                      "text" : "textbox",
                      "boolean" : "checkbox",
                      "choice" : "menulist"
                  }
                  var widget = null;
                  if (convert[field["type"]] == "textbox"){
                      widget = document.getElementById("openplm-fake-tb").cloneNode(true);
                  }else{
                      widget = document.getElementById("openplm-fake-ml").cloneNode(true);
                  }
                  widget.setAttribute("hidden", false);
                  if (field["type"] == "choice"){
                      field["choices"].forEach(function(x){
                              widget.appendItem(x[1], x[0]);
                              });
                  }
                  widget.setUserData("field", field, null);
                  openplm.setWidgetValue(widget, field["initial"]);
                  return widget;
              },

setWidgetValue: function(widget, value){
                    var field = widget.getUserData("field");
                    if (widget.tagName == "textbox"){
                        widget.value = value;
                    }else if (widget.tagName == "checkbox"){
                        widget.checked = value;
                    }else if (widget.tagName == "menulist"){
                        var values = field.choices.map(function(x){return x[0]});
                        var index = values.indexOf(value);
                        widget.selectedIndex = index;
                    }
                },

getWidgetValue: function(widget){
                    if (widget.tagName == "textbox"){
                        return widget.value;
                    }else if (widget.tagName == "checkbox"){
                        return widget.checked;
                    }else if (widget.tagName == "menulist"){
                        if (widget.selectedItem === null){
                            return null;
                        }
                        return widget.selectedItem.value;
                    }
                    return null;
                },

};

window.addEventListener("load", openplm.onLoad, false);
