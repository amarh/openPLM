
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
            if ($("#part_show-" + prefix+ ">span").text() == "+" ){
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
});

