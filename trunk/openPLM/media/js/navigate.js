var edges;
var paper;
function draw_edges(data, width, height){
    var r = Raphael("navholder", width, height);
    var s = r.set();
    $.each(data.edges, function (i,v) {
        var t = r.set()
        var hover_in = function(){
            t.attr("stroke-width", 2);
            t.attr("stroke", "#095b7f");
            $("#" + v.id).addClass("hover");
        };
        var hover_out = function (){
            t.attr("stroke-width", 1.5);
            t.attr("stroke", "#343434");
            $("#" + v.id).removeClass("hover");
        };
        if (v.a !== undefined ){
            var a = r.path("M"+v.a+"z");
            a.attr("fill", "#343434");
            a.hover(hover_in, hover_out);
            t.push(a);
        }
        $("#" + v.id).hover(hover_in, hover_out);
        var e = r.path(v.p);
        e.hover(hover_in, hover_out);
        t.push(e);
        s.push(t);

    });
    s.scale(data.scale[0], data.scale[1], 0, 0);
    s.translate(data.translate[0], data.translate[1]);
    s.attr("stroke", "#343434");
    s.attr("stroke-width", 1.5);
    edges = s;
    paper = r;
} 


function scale_fit_all(){
    var divnav = $("#DivNav");
    var nav = $("#Navigate");
    var nw = nav.width();
    var nh = nav.height();
    var dw = divnav.width();
    var dh = divnav.height();
    var factor = Math.min(Math.min((1.0*(nh-50))/dh, (1.0*(nw-50))/dw), 1);
    scale(factor);
    var origin = "50% 50%";

    divnav.css({
            "left" : (nw - dw) / 2 + "px",
            top: (nh - dh) / 2 + "px",
            "-moz-transform-origin" : origin,
            "-o-transform-origin" : origin,
            "-webkit-transform-origin" : origin,
            "-ms-transform-origin" : origin,
            "transform-origin" : origin
    });
}

var scale_level = 1;
function scale(new_factor) {
    var divnav = $("#DivNav");
    var nav = $("#Navigate");
    var nw = nav.width();
    var left = parseFloat(divnav.css("left"));

    var nh = nav.height();
    var top = parseFloat(divnav.css("top"));
    var orig_x = (nw / 2) - left;
    var orig_y = (nh/2) - top;
    var scale = 'scale(' + new_factor + ')';
    var origin = orig_x + "px " + orig_y + "px"; 
    divnav.css({
            "-moz-transform" : scale,
            "-o-transform" : scale,
            "-webkit-transform" : scale,
            "-ms-transform" : scale,
            "transform" : scale,

            "-moz-transform-origin" : origin,
            "-o-transform-origin" : origin,
            "-webkit-transform-origin" : origin,
            "-ms-transform-origin" : origin,
            "transform-origin" : origin
    });
    scale_level = new_factor;
    $("#slider-scale").slider('value', scale_level*100);
}

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
                    $("<div><a href='"+ url +"'><div> <img src='" + img + "' title='" + title + "' /></div></a></div>"));
                });
            $("#navDocument").text(data["doc"]);
            show_thumbnails_panel($("#" + node_id));
            list.outerHeight(list.parent().innerHeight() - $("#navDocument").outerHeight()-2);
        }
    });
}
dt = display_thumbnails;

function update_nav(focus_node_id, data){
    if (focus_node_id === null){
        focus_node_id = "#" + $("#DivNav div.main_node").attr("id");
    }
    var offset = $(focus_node_id).offset();
    var divNav = $("#DivNav");
    divNav.css("width", data.width+"px");
    divNav.css("height", data.height+"px");
    $("div.node").remove();
    $("div.edge").remove();
    $("#navholder").children().remove();
    $("#add-buttons").children().remove();
    divNav.append(data.divs);
    var submit = $("#FilterNav").find("li").last().clone();
    $("#FilterNavUl").html(data.form);
    $("#FilterNavUl").append(submit);
    $("#add-buttons").html(data.add_buttons);
    make_combobox();
    
    var new_offset = $(focus_node_id).offset();
    var delta_top = new_offset.top - offset.top;
    var delta_left = new_offset.left - offset.left;
    divNav.css({
        left: '-=' + delta_left + "px",
        top: '-=' + delta_top + "px"});
    init();
    draw_edges(data.edges, data.width, data.height);
}

function display_docs(node_id, ajax_url, doc_parts){
    $("#id_doc_parts").attr("value", doc_parts);
    $("#id_update").attr("value", "on");
    $("#Navigate").showLoading();
    $.post(ajax_url,
           $("#FilterNav").find("form").serialize(),
           function(data) {
            update_nav("#" + node_id, data);
            $("#Navigate").hideLoading();
            });
}
dd = display_docs;

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

function reload_page(){
    if (getQueryVariable("add") === "t"){
        location.href = location.href.replace("add=t&", "");
    } else {
        location.reload();
    }
}

function show_add_child(part, form_child_data){
	var id = part.attr("id").split("_");
    var type = id.slice(-2, -1);
    var id = id.slice(-1);
    $.get("/ajax/add_child/" + id + "/",
        form_child_data,
        function (data){
            $("#navAddForm").dialog("option", "buttons", {
                Ok: function() {
                    $.post("/ajax/add_child/"+id+"/",
                        $("#navAddForm>form").serialize(),
                        function (result){
                            if (result.result == "ok"){
                                $("#navAddForm").dialog("close");
                                reload_page();
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
            $("#navAddForm").dialog("option", "width", 500);
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
                                reload_page();
                            }
                        });
                },
                Cancel: function() {
                    $(this).dialog("close");
                }
                
            });
            $("#dialog-confirm>form>table").html(data.form);
            $("#dialog-confirm").dialog("option", "width", 500);
            $("#dialog-confirm").dialog("open");
        }
    );
}

function init(){


        $("div.node").mouseenter(
        function () {
            if (scale_level >= 0.5){
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
                show_add_child($("div.main_node"), form.serialize());
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
            if (result === null) {
                uri_rx = /\/group\/(.*)\/navigate\/?/;
                result = uri_rx.exec(uri);
                uri = "/ajax/navigate/Group/" + (result[1]) + "/-/";
            }
            else {
                uri = "/ajax/navigate/User/" + (result[1]) + "/-/";
            }
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
                    // center the graph to be sure it is visible
                    center();
                    $("#Navigate").hideLoading();
                });
            } );

}

function center(){
    var divNav = $("#DivNav");
    var nav = $("#Navigate");
    var main = divNav.children("div.main_node:first");
    var nw = nav.width();
    var dw = divNav.width();
    var mw = main.width();
    var left = parseInt(main.css("left"));
    var l = (nw - mw) / 2;

    var nh= nav.height();
    var dh = divNav.height();
    var mh = main.height();
    var top = parseInt(main.css("top"));
    var t = (nh - mh) / 2;
    var origin = "50% 50%";

    divNav.css({
            "left" : (l - left) + "px",
            top: (t - top) + "px",
            "-moz-transform-origin" : origin,
            "-o-transform-origin" : origin,
            "-webkit-transform-origin" : origin,
            "-ms-transform-origin" : origin,
            "transform-origin" : origin
    });

};

function getQueryVariable(variable) {
    var query = window.location.search.substring(1);
    var vars = query.split("&");
    for (var i = 0; i < vars.length; i++) {
        var pair = vars[i].split("=");
        if (pair[0] == variable) {
            return unescape(pair[1]);
        }
    }
}


/*
 * enableDragging
 * inspired by http://stackoverflow.com/questions/10965293/dragable-without-jquery-ui/10965447#10965447
 * from Derek
 * CC-By-SA
 */
function enableDragging(ele) {
    var dragging = dragging || false, x, y, Ox, Oy;
    ele.onmousedown = function(ev) {
        dragging = true;
        x = ev.clientX;
        y = ev.clientY;
        Ox = ele.offsetLeft;
        Oy = ele.offsetTop;
        ele.style.cursor = "move";
        window.onmousemove = function(ev) {
            if (dragging) {
                var Sx = ev.clientX - x + Ox,
                    Sy = ev.clientY - y + Oy;
                ele.style.top = Sy + "px";
                ele.style.left = Sx + "px";
                return false;
            }
        };
        window.onmouseup = function(ev) {
            ele.style.cursor = "default";
            dragging = false;
            return false;
        }
    };
}

$(document).ready(function(){

        $('#Navigate').css('overflow', 'hidden');

        $('#rightControl').bind('click', function(){
            $('#DivNav').animate({
                "left": "-=100px"
            }, "fast");
        });

        $('#leftControl').bind('click', function(){
            $('#DivNav').animate({
                "left": "+=100px"
            }, "fast");
        });

        $('#topControl') .bind('click', function(){
            $('#DivNav').animate({
                "top": "+=100px"
            }, "fast");
        });

        $('#bottomControl').bind('click', function(){
            $('#DivNav').animate({
                "top": "-=100px"
            }, "fast");
        });

       enableDragging(document.getElementById("DivNav"));

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

		$( "#slider-scale" ).slider({
			orientation: "vertical",
			range: "min",
			min: 5,
            step: 5,
			max: 200,
			value: 100,
			slide: function( event, ui ) {
				scale(ui.value / 100);
			}
		});
        $("#zoom-fit-all").button().click(scale_fit_all);
        $("#zoom-original").button().click(function (){ center(); scale(1);});
        $("#zoom-in").button().click(function () {
                if (scale_level < 1.95){
                    scale(scale_level + 0.05);
                }});
        $("#zoom-out").button().click(function () {
                if (scale_level > 0.1){
                    scale(scale_level - 0.05);
                }});

        init();
        center();
        if (getQueryVariable("add") === "t") {
            var q = window.location.search.substring(1).replace("add=t&", "");
            show_add_child($("div.main_node"), q);
        }
});