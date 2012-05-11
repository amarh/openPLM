$(
    function (){
        var form = $("#creation_form");
        $("select#id_type").change(
            function (){
               // params is the get parameters
                var params = form.serialize();
                form.showLoading();
                type = $(this).val();
                try {
                    history.replaceState(type, document.title, '?type=' + type);
                } catch (err) {
                    // old browser...
                }
                $.get("/ajax/create/?" + params,  function(data){
                    if (data["reload"]){
                        location = "/object/create/?=" + params;
                    }
                    else {
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
                    make_combobox();
                    $("#reference-title > h2 > span.type").text(data["type"]);
                    form.hideLoading();
                    }
                    });
                });
        }
);
