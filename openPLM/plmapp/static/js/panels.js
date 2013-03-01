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

function hide_search_box(){
    $("#SearchBox").hide();
    $("label[for=SearchButton]").removeClass("ui-state-active");
        hide_left_panel();
    $.cookie("search_box", "false", { path: '/' });
}

function toggle_search_box(){
    var icon = "plus";
    if ($("#SearchBox").is(":hidden")){
        show_search_box();
        icon = "minus";
    }
    else {
        hide_search_box();
    }
    $("#SearchButton").button("option", {
        icons: {
            primary: "ui-icon-" + icon
        },
    });

}



$(function (){
    if ($("#left-col").size() === 0){
        // do not read/set the cookie if the left panel is not present
        hide_left_panel();
        return;
    }
    var search_cookie = $.cookie("search_box");
    var search = search_cookie === "true";
    search = search || $("#SearchBox").hasClass("link_creation");

    $("#SearchButton").attr("checked", search);
    var tb = $("#SearchButton").button( {
        icons: {
            primary: "ui-icon-"+(search ? "minus": "plus")
        },
        text:false
    });
    tb.click(toggle_search_box);
    $("#ToggleBoxButton > label").addClass("ui-corner-right").removeClass("ui-corner-all");

    var close_search_box = $("<button>close</button>");
    var button = close_search_box.button({
        icons: {
                primary: "ui-icon-close"
        },
        text:false
        }).click(toggle_search_box);
    var li = $("<li/>");
    li.append(button);
    $("#SearchBox h2>div.toolbar>ul").append(li);


    if (search){
        show_search_box();
    }
    else{
        hide_search_box();
    }
    if (search_cookie !== null){
        $.cookie("search_box", search_cookie, { path: '/' });
    }


});
