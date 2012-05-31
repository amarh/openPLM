/**
 * Add a confirmation dialog on forms which have a 'confirmation' class
 * each form must have and id and a div which id is 'formID-dialog' must 
 * be present. This div is used to build a dialog with jquery ui.
 * The form must have at least one submit button with a valid name.
 * It can have several submit buttons.
 */

function confirm_submit(form, e) {

    if (form.hasClass("confirmed")){
        return true;
    }
    e.preventDefault();
    $("#" + form.attr("id") + "-dialog" ).dialog({
			resizable: false,
			modal: true,
            width: 600,
			buttons: {
				Cancel: function() {
					$( this ).dialog( "close" );
				},
				Yes: function() {
					$( this ).dialog( "close" );
                    form.addClass("confirmed");
                    var button = $("input[type=submit][clicked=true]");
                    $("<input>").attr({
                        'type':'hidden',
                        'name': button.attr('name')
                    }).val(button.val()).appendTo(form);
                    $(this).find("input").hide().appendTo(form);                    
                    form.submit();
				}
			}
		});
	$("#" + form.attr("id") + "-dialog").on('keydown',function(a){
        if( a.keyCode == $.ui.keyCode.ENTER ) {
            $( this ).dialog( "close" );
            form.addClass("confirmed");
            var button = $("input[type=submit][clicked=true]");
            $("<input>").attr({
                'type':'hidden',
                'name': button.attr('name')
            }).val(button.val()).appendTo(form);
            $(this).find("input").hide().appendTo(form);                    
            form.submit();;
        }
    });
    return false;

}

$(
    function(){
        $("form.confirmation input[type=submit]").click(function() {
            $("input[type=submit]", $(this).parents("form")).removeAttr("clicked");
            $(this).attr("clicked", "true");
        });
        $("form.confirmation").submit(
            function (e) {
                return confirm_submit($(this), e);
            }
        );
        $("form.confirmation").each(function (){
            var form = $(this);
            var dialog = $("#" + form.attr("id") + "-dialog" );
            dialog.hide();
            if (dialog.hasClass("c-error")){
                var cls = dialog.attr("class").split(" ");
                var actions = $.grep(cls, function(x){return /^action-/.test(x);});
                if (actions.length > 0) {
                    var action = actions[0].replace(/^action-/, ""); 
                    form.find("input[type=submit][name=" + action +"]").click();
                }
            }
        });


    }
);
