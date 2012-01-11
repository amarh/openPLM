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
			height:250,
			modal: true,
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
                    form.submit();
				}
			}
		});
    return false;

}

$(
    function(){
        $(".confirmation input[type=submit]").click(function() {
            $("input[type=submit]", $(this).parents("form")).removeAttr("clicked");
            $(this).attr("clicked", "true");
        });

        $(".confirmation").submit(
            function (e) {
                return confirm_submit($(this), e);
            }
        );

    }
);
