
function update_part_form() {
    var form = $("#decompose_form");
    form.showLoading();
    var prefix = $(this).attr("id").replace("-type_part", "").replace("id_", "");
    var params = form.serialize();
    $.ajax({
        url: "/ajax/decompose/"+prefix + "/?" + params,
        success: function( part_form ){
            $("#extra_part_" + prefix).html(part_form);
            if ($("#part_show" + prefix.replace("form-", "")+ ">span").text() == "+" ){
                $("#part_show" + prefix.replace("form-", "")).click();
            }
            make_combobox();
            form.hideLoading();
            }
    });
}

    

$(function() {
    $("#decompose_form button.toggle_extra_attributes_button").button().click(
        function () {
            var id = $(this).attr("id");
            $("tr." + id).toggle();
            $(this).children("span").text($(this).children("span").text() == "+" ? "-" : "+");
            return false;
        }
    );
    $("#decompose_form td.part_type_form > select").change(update_part_form);
    }
 );

