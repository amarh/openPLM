$(document).ready(
        function (){
        // update the search form when a new type is selected
        $("#search_table > tbody > tr > td > #id_type").change(
            function(){
                // params is the get parameters
                var params = $("#search_form").serialize();
                $.get("/ajax/search/?" + params,  function(data){
                    var rows = $("#search_table > tbody");
                    // remove old form
                    rows.find("tr").each(function(index, row){
                        if (index != 0){
                            $(row).remove();
                        }
                    }
                    );
                    // add the new form
                    $("#search_table > tbody").append(data);
                    });
                });
        }
);
