
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
            $.each(data["files"], function(index, value){
                var name = value[0];
                var url = value[1];
                var img = value[2];
                var title = "Download " + name;
                $("#thumbnailsList").append(
                    $("<a href='"+ url +"'> <img src='" + img + "' width='160' height='160' title='" + title + "' /></a>"));
                });
            $("#navDocument").text(data["doc"]);
            show_thumbnails_panel($("#" + node_id));
        }
    });
}

function update_nav(focus_node_id, data){
    var offset = $(focus_node_id).offset();
    var date = new Date();
    var divNav = $("#DivNav");
    $("#ImgNav").attr("src", data["img"] + '?v=' + date.getTime());
    $("#ImgNav").load(
         function() {
            $("div.node").remove();
            divNav.append(data.divs);
            var submit = $("#FilterNav").find("li").last().clone();
            $("#FilterNavUl").html(data.form);
            $("#FilterNavUl").append(submit);
            var new_offset = $(focus_node_id).offset();
            var delta_top = new_offset.top - offset.top;
            var delta_left = new_offset.left - offset.left;
            divNav.css({
                left: '-=' + delta_left+"px",
                top: '-=' + delta_top + "px"});
            init();
    });
}

function display_docs(node_id, ajax_url, doc_parts){
    $("#id_doc_parts").attr("value", doc_parts);
    $("#id_update").attr("value", "on");
    $.post(ajax_url,
           $("#FilterNav").find("form").serialize(),
           function(data) {update_nav("#" + node_id, data);});
}


function show_add_child(part, form_child){
	var id = part.attr("id").split(":");
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
        // TODO : documents, check if selected part can be added
        $("div.main_node").droppable({
			accept: "tr.Content",
			activeClass: "drop_active",
			hoverClass: "drop_hover",
			drop: function( event, ui ) {
                show_add_child($(this), $("form", ui.draggable));
			}
		});

}

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


        // double click mode
        var divNav = $("#DivNav");
        var navigate = $("#Navigate");
        var OFFSET = 100;
        var timeout = null;
        var move = false;
        function clear_move_event(){
            if (timeout != null ){
                window.clearTimeout(timeout);
                timeout = null;
            }
        }
        navigate.mousemove(function (e){
            if (move){
                var center_x = navigate.offset().left + navigate.width() / 2; 
                var center_y = navigate.offset().top + navigate.height() / 2;
                var vx = (center_x - e.pageX);
                var vy = (center_y - e.pageY);
                clear_move_event();
                if ((Math.abs(vx) > OFFSET || Math.abs(vy) > OFFSET)){
                    var f = function(count){
                        if (count > 0){
                            divNav.css({left: '+=' + (vx * 0.03)  + "px",
                                top: "+=" + (vy  * 0.03) + "px"});
                            timeout = window.setTimeout(f, 20, count-1);
                        }
                        };
                    f(40);
                    }
                }
            }
        );

        navigate.dblclick(function(evt){
            clear_move_event();
            if (evt.button == 0){
                move = ! move;
            }
            else {
                move = false;
            }

        });
        navigate.mouseleave(function (){
                clear_move_event();
                } );

        // add on drag and drop
        $("tr.Content").add("tr.Content2").css("z-index", "99");
        $("tr.Content").add("tr.Content2").draggable({ helper: 'clone' });
        $("#navAddForm").dialog({
                autoOpen: false,
			height: 300,
			width: 350,
			modal: true,
			close: function() {
			}
		});

        init();
});
