
function update_part_form() {
    var prefix = $(this).attr("id").replace("-type_part", "").replace("id_", "");
    var params = $("#decompose_form").serialize();
    $.ajax({
        url: "/ajax/decompose/"+prefix + "/?" + params,
        success: function( part_form ){
            $("#extra_part_" + prefix).html(part_form);
            if ($("#part_show" + prefix.replace("form-", "")).attr("value") == "+" ){
                $("#part_show" + prefix.replace("form-", "")).click();
            }
            make_combobox();
            }
    });
}

    

$(function() {
        $("#decompose_form input.toggle_extra_attributes_button").button()
            .css({"padding": "0.2em"}).click(
            function () {
                var id = $(this).attr("id");
                $("tr." + id).toggle();
                $(this).attr("value", ($(this).attr("value") == "+") ? "-" : "+");
            }
        );
        $("#decompose_form td.part_type_form > select").change(update_part_form);
        }
 );

