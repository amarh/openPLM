function hide_left_panel(){
    $("div.left-col").hide();
    $("div.center-col").css("margin-left", "0");
}

function show_left_panel(){
    $("div.left-col").show();
    $("div.center-col").css("margin-left", "330px");
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
    if ($("#SearchBox").is(":hidden")){
        hide_left_panel();
    }
    $.cookie("create_box", "false", { path: '/' });
}

function hide_search_box(){
    $("#SearchBox").hide();
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
