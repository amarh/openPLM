function Plugin(){
    this.username = "";
    this.password = "";
    this.SERVER =  "http://localhost:8000/"; 
    this.xrequest = new XMLHttpRequest();

    // methods
    this.login = login;
    this.send_post = send_post;
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

var PLUGIN = new Plugin();

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

  onToolbarButtonCommand: function(e) {
    // just reuse the function above.  you can change this, obviously!
    openplm.onMenuItemCommand(e);
  }
};

window.addEventListener("load", openplm.onLoad, false);
