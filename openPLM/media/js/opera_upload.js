
function opera_add_in_queue(input){
    hide(input);
    $('form.hidden').append(input);
}

//multiple selection in inputs file disable
function opera_prepare_form(inputs_file){
    $.each(inputs_file,function(id,input){
        var f_key = input.files[0].name;
        f_key = f_key.replace(".","_");
        $(input).attr("name",files_info[f_key].field_name);
        $(input).attr("id","id_"+files_info[f_key].field_name);
    });
}

//init the form (input's name and id), and submit it
function opera_up_file(f_form,new_action,go_to){
    $(f_form).attr("action",new_action);
    $(f_form).attr("target","hidden_frame");
    var hidden_frame=$("<iframe id='hidden_frame' class='hidden' ></iframe>");
    $("#add_file_container").append(hidden_frame);
    $(f_form).submit();
    $(f_form).attr("action","");
}

