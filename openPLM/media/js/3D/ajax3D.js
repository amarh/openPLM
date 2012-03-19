
       function update_form(dat,id){

            var params = $("#decompose_form").serialize();
            $.ajax({
                url: "/ajax/decompose/?" + params,
                success: function( new_data ) {

                
                var $new_form = jQuery(new_data);
                
                $new_form.find("input").each(function(index, element){
                

                  if ($('#'+element.id).val()){
                        element.value=$('#'+element.id).val();
                        }                                             
                });
                $new_form.find("select").each(function(index, element){
                        if ($('#'+element.id).val() && element.className!="selector"){
                        element.value=$('#'+element.id).val();

                       }                                                  
                });
                $new_form.find("textarea").each(function(index, element){
                        if ($('#'+element.id).val()){
                        element.value=$('#'+element.id).val();

                       }                                                  
                });
                

                

                $new_form.find(".show_hide").each(function(index, element){
                             name=element.className.replace(" show_hide", "");
                             if($('#'+name).val()=="+")
                             element.style.display="none";
                             else{
                             element.style.display="";
                             }

                        
   
                });


                var number=parseInt(dat.name[5])+1
                tr_pressed=id+number;

                $new_form.find("#"+tr_pressed).each(function(index, element){

                         element.value="-";              

                });
                $new_form.find("."+tr_pressed).each(function(index, element){

                         element.style.display="";              

                });

                $('#decompose_form').empty();
                $("#decompose_form").append($new_form);
                

                $("select").chosen();
                
                
                }});



	             
	        };
