var topics = {};

jQuery.Topic = function( id ) {
    var callbacks,
        method,
        topic = id && topics[ id ];
    if ( !topic ) {
        callbacks = jQuery.Callbacks();
        topic = {
            publish: callbacks.fire,
            subscribe: callbacks.add,
            unsubscribe: callbacks.remove
        };
        if ( id ) {
            topics[ id ] = topic;
        }
    }
    return topic;
};

function hide_left_panel(){
    $("div#left-col").hide();
    if ($("div#center-col").css("margin-left") === "330px" ){
        $("div#center-col").css("margin-left", "0");
        $.Topic("hide_left_panel").publish();
    }
}

function show_left_panel(){
    $("div#left-col").show();
    if ($("div#center-col").css("margin-left") != "330px" ){
        $("div#center-col").css("margin-left", "330px");
        $.Topic("show_left_panel").publish();
    }
}

function show_create_box(){
    $("#CreationBox").show();
    show_left_panel();
    $.cookie("create_box", "true", { path: '/' });
}

function show_search_box(){
    $("#SearchBox").show();
    show_left_panel();
    $.cookie("search_box", "true", { path: '/' });
}

function hide_create_box(){
    $("#CreationBox").hide();
    $("label[for=CreationButton]").removeClass("ui-state-active");
    if ($("#SearchBox").is(":hidden")){
        hide_left_panel();
    }
    $.cookie("create_box", "false", { path: '/' });
}

function hide_search_box(){
    $("#SearchBox").hide();
    $("label[for=FindButton]").removeClass("ui-state-active");
    if ($("#CreationBox").is(":hidden")){
        hide_left_panel();
    }
    $.cookie("search_box", "false", { path: '/' });
}

function toggle_create_box(){
    if ($("#CreationBox").is(":hidden")){
        show_create_box();
    }
    else {
        hide_create_box();
    }
}



function toggle_search_box(){
    if ($("#SearchBox").is(":hidden")){
        show_search_box();
    }
    else {
        hide_search_box();
    }
}



$(function (){

    var search = $.cookie("search_box") === "true";
    var create = $.cookie("create_box") === "true";

    $("#FindButton").attr("checked", search);
    $("#CreationButton").attr("checked", create);
    $("#FindButton").button().click(toggle_search_box);
    $("#CreationButton").button().click(toggle_create_box);


    var close_creation_box = $("<button>close</button>");
    var button = close_creation_box.button({
        icons: {
                primary: "ui-icon-close"
        },
        text:false
        }).click(toggle_create_box);
    var li = $("<li/>");
    li.append(button);
    $("#CreationBox h2>div.toolbar>ul").append(li);

    var close_search_box = $("<button>close</button>");
    button = close_search_box.button({
        icons: {
                primary: "ui-icon-close"
        },
        text:false
        }).click(toggle_search_box);
    li = $("<li/>");
    li.append(button);
    $("#SearchBox h2>div.toolbar>ul").append(li);


    if (search){
        show_search_box();
    }
    else{
        hide_search_box();
    }
    if (create){
        show_create_box();
    }
    else{
        hide_create_box();
    }

});
