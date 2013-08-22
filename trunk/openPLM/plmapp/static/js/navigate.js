var edges;
var paper;
var past;
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
    $.cookie("navigate_scale", scale_level, { path: '/' });
}

function show_thumbnails_panel(node){
    if ($("#navThumbnails").is(":hidden")) {
        $("#navThumbnails").show();
        $("#FilterNav, #RevisionsNav, #full-screen").css("right", "190px");
        var width = node.width();
        if (node.offset().left + width > $("#navThumbnails").offset().left){
            var left = $("#DivNav").position().left - 180;
            $("#DivNav").css("left", left);
        }
    }
}

function hide_thumbnails_panel(){
    $("#navThumbnails").hide();
    $("#FilterNav, #RevisionsNav, #full-screen").css("right", "10px");
}
var escapeHTML = (function () {
    'use strict';
    var chr = { '"': '&quot;', '&': '&amp;', '<': '&lt;', '>': '&gt;' };
    return function (text) {
        return text.replace(/[\"&<>]/g, function (a) { return chr[a]; });
    };
}());
function display_thumbnails(node_id, ajax_url){
    $("#thumbnailsList").empty();
    $.ajax({
        url: ajax_url,
        success: function( data ) {
            var list = $("#thumbnailsList");
            var div, name, title;
            $.each(data["files"], function(index, value){
                name = escapeHTML(value.name);
                if (value.deleted) {
                    div = "<div><span>" + name + " - deleted</span></div>";
                } else {
                    title = "Download " + name;
                    if (value.deprecated) {
                        title += " ! deprecated !";
                    }
                    div = "<div><a href='"+ value.url +"'><div> <img src='" + value.img + "' title='" + title + "' /><span>" + name + "</span></div></a></div>";
                }
                list.append($(div));
            });
            $("#navDocument").text(data["doc"]);
            show_thumbnails_panel($("#" + node_id));
            list.outerHeight(list.parent().innerHeight() - $("#navDocument").outerHeight()-6);
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
    past = data["past"];
    if (! past){
        $("#add-buttons").html(data.add_buttons);
    }
    make_combobox();
    
    var new_offset = $(focus_node_id).offset();
    var delta_top = new_offset.top - offset.top;
    var delta_left = new_offset.left - offset.left;
    divNav.css({
        left: '-=' + delta_left + "px",
        top: '-=' + delta_top + "px"});
    init();
    hide_thumbnails_panel();
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
        $( "#id_date" ).datepicker();

        $("div.node").mouseenter(
        function () {
            if (scale_level >= 0.5){
                $(this).find(".node-toolbar").show();
            }
        }); 
        $("div.node").mouseleave(
        function () {
            $(this).find(".node-toolbar").hide();
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

        if (! past){
            $("li.Result div.toolbar").show();
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

        }else {
            $("li.Result div.toolbar").hide();
        }

        $( ".node_thumbnails" ).button({
            icons: {
                primary: "ui-icon-document"
            },
            text: false
        });

        $( ".node_show_docs.add" ).button({
            icons: {
                primary: "ui-icon-plus"
            },
            text: false
        });
        $( ".node_show_docs.remove" ).button({
            icons: {
                primary: "ui-icon-minus"
            },
            text: false
        });

        $( ".study-btn" ).button({
            icons: {
                primary: "ui-icon-pencil"
            },
            text: false
        });
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
                uri_rx = /\/(group|ecr)\/(.*)\/navigate\/?/;
                result = uri_rx.exec(uri);
                t = {"ecr": "ECR", "group": "Group"}
                uri = "/ajax/navigate/"+ t[result[1]] +  "/" + (result[2]) + "/-/";
            }
            else {
                uri = "/ajax/navigate/User/" + (result[1]) + "/-/";
            }
        }
        else {
            uri = "/ajax/navigate/" + (result[1])  + "/";
        }
        $("#FilterButton").click(function () {
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

// https://gist.github.com/1330150
$.fn.draggable2 = function() {
    var $document = $(document)
    , mouse = { update: function(e) {this.x = e.pageX; this.y = e.pageY;} };

    return this.each(function(){
        var $elem = $(this);
        $elem.bind('mousedown.drag', function(e) {
            mouse.update(e);
            $elem.css("cursor", "move");
            if ( !/^(relative|absolute)$/.test($elem.css('position') ) ) {
                $elem.css('position', 'relative');
            }
            var links = $elem.find("a");
            var buttons = $elem.find("button");
            var click_prevented = false;
            $document.bind('mousemove.drag', function(e) {
                if (e.pageX - mouse.x == 0 && e.pageY - mouse.y == 0)
                    return;
                if (! click_prevented ){
                    links.bind("click.prevent", function(event) { event.preventDefault(); });
                    buttons.each(function (i){
                        $(this).attr("data-onclick", $(this).attr("onclick"));
                        $(this).attr("onclick", "");
                    });
                    click_prevented = true;
                }
                $elem.css({
                    left: (parseInt($elem.css('left'))||0) + (e.pageX - mouse.x) + 'px',
                    top: (parseInt($elem.css('top'))||0) + (e.pageY - mouse.y) + 'px'
                });
                mouse.update(e);
                e.preventDefault();
            });
            $document.one('mouseup.drag', function(e) {
                $elem.css("cursor",  "default");
                window.setTimeout(function() {
                    links.unbind("click.prevent");
                    buttons.each(function (i){
                        $(this).attr("onclick", $(this).attr("data-onclick"));
                    });
                }, 300);
                $document.unbind('mousemove.drag');
                e.preventDefault();
            });
            e.preventDefault();
        });
    });
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

        $("#DivNav").draggable2();

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
            out: function() {
                if (! $("#ui-datepicker-div").is(":visible")){
                    $("#FilterNav ul").hide();
                }
            },
            timeout: 500
        });
        
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
            }
        });
        $("#zoom-out").button().click(function () {
            if (scale_level > 0.1){
                scale(scale_level - 0.05);
            }
        });

        if (screenfull.enabled) {
            $("#full-screen").click(function() {
                var main = document.getElementById("main_content");
                screenfull.toggle(main);
            });
        } else {
            $("#full-screen").hide();
        }
        var width = $("#main_content").width();
        var height = $("#main_content").height();
        screenfull.onchange = function() {
            var main = $(window);
            var w, h;
            if( screenfull.isFullscreen ) {
                w = main.width() +"px";
                h = main.height() +"px";
                $("#main_content, #Navigate").css({"width": w, "height": h});
            } else {
                $("#main_content, #Navigate").css({"width": "inherit", "height": height+"px"});
            }
            var list = $("#thumbnailsList");
            list.outerHeight(list.parent().innerHeight() - $("#navDocument").outerHeight()-6);
            center();
        };


        init();
        center();
        var saved_level = $.cookie("navigate_scale");
        if (saved_level > 0) {
            scale(saved_level);
        }
        if (getQueryVariable("add") === "t") {
            var q = window.location.search.substring(1).replace("add=t&", "");
            show_add_child($("div.main_node"), q);
        }
});
