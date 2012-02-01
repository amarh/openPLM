
function show_thumbnails_panel(node){
    if ($("#navThumbnails").is(":hidden")) {
        $("#navThumbnails").show();
        $("#FilterNav").css("right", "190px");
        var width = node.width();
        if (node.offset().left + width > $("#navThumbnails").offset().left){
            var left = $("#DivNav").position().left - 180;
            $("#DivNav").css("left", left);
        }
    }
}

function hide_thumbnails_panel(){
    $("#navThumbnails").hide();
    $("#FilterNav").css("right", "10px");
}

function display_thumbnails(node_id, ajax_url){
    $("#thumbnailsList").empty();
    $.ajax({
        url: ajax_url,
        success: function( data ) {
            var list = $("#thumbnailsList");
            $.each(data["files"], function(index, value){
                var name = value[0];
                var url = value[1];
                var img = value[2];
                var title = "Download " + name;
                list.append(
                    $("<div><a href='"+ url +"'> <img src='" + img + "' width='160' height='160' title='" + title + "' /></a></div>"));
                });
            $("#navDocument").text(data["doc"]);
            show_thumbnails_panel($("#" + node_id));
            list.outerHeight(list.parent().innerHeight() - $("#navDocument").outerHeight()-2);
        }
    });
}

function update_nav(focus_node_id, data){
    if (focus_node_id != null)
        var offset = $(focus_node_id).offset();
    var date = new Date();
    var divNav = $("#DivNav");
    $("#ImgNav").css("width", data.width+"px");
    $("#ImgNav").css("height", data.height+"px");
    divNav.css("width", data.width+"px");
    divNav.css("height", data.height+"px");
    var path = data["img"] + '?v=' + date.getTime();
    $("#ImgNav").css("background", 'url("'+path+'") no-repeat 0 0');
    $("div.node").remove();
    divNav.append(data.divs);
    var submit = $("#FilterNav").find("li").last().clone();
    $("#FilterNavUl").html(data.form);
    $("#FilterNavUl").append(submit);
    $("#FilterNavUl select").css("width", "12em");
    $("#FilterNavUl select").chosen({disable_search_threshold: 7});
    $("#FilterNavUl div.chzn-container").addClass("ui-widget ui-button ui-state-default ui-corner-all")
    $("#FilterNavUl div.chzn-container-single").addClass("selector");
    if (focus_node_id != null){
        var new_offset = $(focus_node_id).offset();
        var delta_top = new_offset.top - offset.top;
        var delta_left = new_offset.left - offset.left;
        divNav.css({
            left: '-=' + delta_left + "px",
            top: '-=' + delta_top + "px"});
        }
    else {
        var nw = $("#Navigate").innerWidth();
        var nh = $("#Navigate").innerHeight();
        divNav.css({left: (nw / 2 - data.center_x) + "px",
                    top: (nh / 2 - data.center_y) + "px"});
    }
    init();
}

function display_docs(node_id, ajax_url, doc_parts){
    $("#id_doc_parts").attr("value", doc_parts);
    $("#id_update").attr("value", "on");
    $.post(ajax_url,
           $("#FilterNav").find("form").serialize(),
           function(data) {update_nav("#" + node_id, data);});
}

function can_add_child(part, form_child, cache){
    var form = form_child.serialize();
    if (form in cache){
        return cache[form];
    }
    var id = part.attr("id").split("_");
    var type = id.slice(-2, -1);
    var id = id.slice(-1);
    var can = false;
    if (type == "Part"){
        $.ajaxSetup({async : false});

        $.get("/ajax/can_add_child/" + id + "/",
            form,
            function (result){
                can = result.can_add;
            }
            );
        $.ajaxSetup({async : true});
    }
    cache[form] = can;
    return can;
}

function can_attach(plmobject, form_child, cache){
    var form = form_child.serialize();
    if (form in cache){
        return cache[form];
    }
    var id = plmobject.attr("id").split("_");
    var type = id.slice(-2, -1);
    var id = id.slice(-1);
    var can = false;
    
    if (type == "Part" || type == "Document"){
        $.ajaxSetup({async : false});
        $.get("/ajax/can_attach/" + id + "/",
            form,
            function (result){
                can = result.can_attach;
            }
            );
        $.ajaxSetup({async : true});
    }
    cache[form] = can;
    return can;
}

function show_add_child(part, form_child){
	var id = part.attr("id").split("_");
    var type = id.slice(-2, -1);
    var id = id.slice(-1);
    $.get("/ajax/add_child/" + id + "/",
        form_child.serialize(),
        function (data){
            $("#navAddForm").dialog("option", "buttons", {
                Ok: function() {
                    $.post("/ajax/add_child/"+id+"/",
                        $("#navAddForm>form").serialize(),
                        function (result){
                            if (result.result == "ok"){
                                $("#navAddForm").dialog("close");
                                location.reload();
                            }
                            else if (result.error == "invalid form") {
                                $("#navAddForm>form>table").html(result.form);

                            }
                        });
                },
                Cancel: function() {
                    $(this).dialog("close");
                }
                
            });
            $("#navAddForm>form>table").html(data.form);
            $("#navAddForm").dialog("open");
        }
    );
}

function show_attach(plmobject, form_child){
	var id = plmobject.attr("id").split("_");
    var type = id.slice(-2, -1);
    var id = id.slice(-1);
    
    $.get("/ajax/attach/" + id + "/",
        form_child.serialize(),
        function (data){
            $("#dialog-confirm").dialog("option", "buttons", {
                Ok: function() {
                    $.post("/ajax/attach/"+id+"/",
                        $("#dialog-confirm>form").serialize(),
                        function (result){
                            if (result.result == "ok"){
                                $("#dialog-confirm").dialog("close");
                                location.reload();
                            }
                        });
                },
                Cancel: function() {
                    $(this).dialog("close");
                }
                
            });
            $("#dialog-confirm>form>table").html(data.form);
            $("#dialog-confirm").dialog("open");
        }
    );
}

function init(){
        $("div.node").mouseenter(
        function () {
            if (! ($(this).hasClass("drop_active") || $(this).hasClass("drop_hover"))){
                $(this).find(".node_thumbnails").show();
                $(this).find(".node_show_docs").show();
            }
        }); 
        $("div.node").mouseleave(
        function () {
            $(this).find(".node_thumbnails").hide();
            $(this).find(".node_show_docs").hide();
        }
        );

        $("#closeThumbnails").button({
            icons : {
                primary: 'ui-icon-close'
                },
            text: false}).click(hide_thumbnails_panel);

        var config = {    
             over: function(){
                 if ($("#navThumbnails").is(":visible"))
                       $(this).click();}, // function = onMouseOver callback (REQUIRED)    
             timeout: 500, // number = milliseconds delay before onMouseOut    
             out: function(){} // function = onMouseOut callback (REQUIRED)    
        };
        $(".node_thumbnails").hoverIntent(config);

        // add stuff
        var cache1 = new Object();
        var cache2 = new Object();
        var main_node = $("div.main_node");
        $("li.Result").hoverIntent(
            function() { 
                var li = $(this);
                var form = li.children("form").first();
                var add = can_add_child(main_node, form, cache1);
                li.find("div.toolbar > button.add_child").button("option", "disabled", !add).button( "refresh" );
                var attach = can_attach(main_node, form, cache2);
                li.find("div.toolbar > button.attach").button("option", "disabled", !attach).button( "refresh" ); 

            },
            function() { 
                $(this).find("div.toolbar > button").button("disable").button( "refresh" );
            }
        );

        $("button.add_child").button({
                icons: {
                    primary: "ui-icon-plus"
                },
                text: false,
                disabled: true
            }).click(
            function () {
                var form = $(this).closest("li.Result").children("form");
                show_add_child($("div.main_node"), form);
            }
        );
        
        $("button.attach").button({
                icons: {
                    primary: "ui-icon-link"
                },
                text: false,
                disabled: true
            }).click(
            function () {
                var form = $(this).closest("li.Result").children("form");
                show_attach($("div.main_node"), form);
            }
        );
        
       
        $("#FilterNav").find("form").submit(function (e){
                return false;
        });
        var uri = new String(document.location);
        var uri_rx = /\/object\/(.*)\/navigate\/?/;
        var result = uri_rx.exec(uri);
        if (result === null){
            uri_rx = /\/user\/(.*)\/navigate\/?/;
            result = uri_rx.exec(uri);
            uri = "/ajax/navigate/User/" + (result[1]) + "/-/";
        }
        else {
            uri = "/ajax/navigate/" + (result[1])  + "/";
        }
        $("#FilterButton").button().click(function () {
            $("#Navigate").showLoading();
            $.post(uri,
                $("#FilterNav").find("form").serialize(),
                function (data) {
                    update_nav(null, data);
                    $("#Navigate").hideLoading();
                });
            } );

}

function center(){
    var nw = $("#Navigate").width();
    var dw = $("#DivNav").width();
    $("#DivNav").css({"left":((nw-dw)/2)+"px"});  

};

$(document).ready(function(){

        // Supprime la scrollbar en JS
        $('#Navigate').css('overflow', 'hidden');

        // crée un écouteur pour l'évènement de type clic sur les div qui ont l' id #rightControl
        $('#rightControl')
        .bind('click', function(){
            // Move slideInner using left attribute for position
            $('#DivNav').animate({
                "left": "-=100px"
                }, "fast");
            });

        // crée un écouteur pour l'évènement de type clic sur les div qui ont l' id #leftControl
        $('#leftControl')
        .bind('click', function(){
            // Move slideInner using left attribute for position
            $('#DivNav').animate({
                "left": "+=100px"
                }, "fast");
            });

        // crée un écouteur pour l'évènement de type clic sur les div qui ont l' id #topControl
        $('#topControl')
            .bind('click', function(){
                    // Move slideInner using top attribute for position
                    $('#DivNav').animate({
                        "top": "+=100px"
                        }, "fast");
                    });

        // crée un écouteur pour l'évènement de type clic sur les div qui ont l' id #bottomControl
        $('#bottomControl')
            .bind('click', function(){
                    // Move slideInner using left attribute for position
                    $('#DivNav').animate({
                        "top": "-=100px"
                        }, "fast");
                    });

        $("#DivNav").draggable({
cursor: 'crosshair'
});


        $("#navAddForm").dialog({
            autoOpen: false,
			height: 300,
			width: 350,
			modal: true,
		});
        $("#dialog-confirm").dialog({
            autoOpen: false,
			height: 300,
			width: 350,
			modal: true,
		});

        $("#FilterNav").hoverIntent({
            over: function() { $("#FilterNav ul").show();},
            out: function() { $("#FilterNav ul").hide();},
            timeout: 500
             } );
        
        $.Topic("show_left_panel").subscribe(function (){
                $("#DivNav").css({left : "-=330px"});
        });
        $.Topic("hide_left_panel").subscribe(function (){
                $("#DivNav").css({left : "+=330px"});
        });
        init();
        center();
});
