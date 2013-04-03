
function update_part_form() {
    var form = $("#decompose_form");

    form.showLoading();
    var prefix = $(this).attr("id").replace("-type_part", "").replace("id_", "");

    var assembly_reference = $(this).parent().attr("id").replace("_ref", "");  
    var selected=$(this).val()

    var params = form.serialize();
    $.ajax({
        url: "/ajax/decompose/"+prefix+"/?" + params,
        success: function( part_form ){
            $("#extra_part_form-"+ prefix).html(part_form);
            if ($("#part_show-" + prefix).text() == "+" ){
                $("#part_show-" + prefix).click();
            }


            $("#decompose_form a#"+assembly_reference+"_part").html("("+selected+")")
            make_combobox();
            form.hideLoading();
        }
    });
}


$(document).ready(function() {
    $("#decompose_form button.toggle").click(
        function () {
            var id = $(this).attr("id");
            $("tr." + id).toggle();
            $(this).text($(this).text() == "+" ? "-" : "+");
            return false;
        }
    );
    $("#decompose_form td.part_type_form > select").change(update_part_form);

    // display or hide all assembly at the level of the span clicked
    $("span.display_level").click(function(){
        var level = $(this).parent().attr("id");
        var td_level = $("td[level^="+level+"]");
        var open;
        $(this).parent().hasClass("open")? open=true : open=false;
        $.each(td_level,function(index,value){
            if($(value).hasClass("open")===open)
                $(value).find("span").click();
        });
        $(this).parent().toggleClass("open");
    });

    // display or hide one assembly
    $("span.display_name").click(function (){
        level = $(this).parent().attr("level");
        $('tr[name^=part'+level+']').toggleClass("hidden");
        $('tr[name^=doc'+level+']').toggleClass("hidden");
        $(this).parent().toggleClass("open");
    });

    // display or hide the assembly corresponding to the part
    $("a.display").click(function (){
        //$(this).attr("href") return '#name' where name is the name of the assembly
        var id_ref=$(this).attr("href").substr(1);
        var array=$("td.assembly_name");
        $.each(array, function(index, value){
            if(value.id === id_ref)
                $(value).find("span").click();
        });
    });

    // display description of a part (type, document, name ....)
    $("a.indexed").click(function(){
        var t_body = $(this).parent().parent().parent();
        var name_ref=$(this).attr("name");
        //$(this).attr("name") return 'name' where name is the name of the part
        var array = $(t_body).children("tr.part").children("td").children('p[name=ref_'+name_ref+']');
        $.each(array, function(index, value){
            if($(value).attr("name").substr(4) === name_ref){
                var level=$(value).parent().parent().attr("level");
                var td_level = $("td[level="+level.substring(0,2)+"]");
                if($(td_level).hasClass("open") == false)
                    $(td_level).find("span").click();
            }
        });
    });
});

