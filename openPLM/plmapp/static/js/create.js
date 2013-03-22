$(
    function (){
        var form = $("#creation_form");
        if($("#id_auto").attr("checked")=="checked"){
            $("#id_reference").attr("disabled","disabled");
        }
        $("select#id_type").change(
            function (){
                // params is the get parameters
                var params = form.serialize();
                form.showLoading();
                type = $(this).val();
                $.get("/ajax/create/?" + params,  function(data){
                    if (data["reload"]){
                        location = "/object/create/?=" + params;
                    }
                    else {
                        try {
                            history.replaceState(type, document.title, '?type=' + type);
                        } catch (err) {
                            // old browser...
                        }
                        var rows = form.find("tbody");
                        // remove old form
                        rows.find("tr").each(function(index, row){
                            if (index != 0){
                                $(row).remove();
                            }
                        }
                    );
                    // add the new form
                    form.find("tbody").append(data["form"]);
                    form.find("tbody").append(data["form_media"]);
                    make_combobox();
                    $("#reference-title > h2 > span.type").text(data["type"]);
                    form.hideLoading();
                }
                if($("#id_auto").attr("checked")=="checked"){
                    $("#id_reference").attr("disabled","disabled");
                }
                $("#id_auto").change(function(){
                    if ($("#id_auto").attr("checked")=="checked"){
                        $("#id_reference").attr("disabled","disabled");
                    }else{
                        $("#id_reference").removeAttr("disabled");
                    }
                });
            });
        });
        $("#id_auto").change(
            function(){
                if ($("#id_auto").attr("checked")=="checked"){
                    $("#id_reference").attr("disabled","disabled");
                }else{
                    $("#id_reference").removeAttr("disabled");
                }
            }
        );
    }
);
