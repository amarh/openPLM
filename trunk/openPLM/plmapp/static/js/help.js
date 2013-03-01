$(
    function () {
        var dialog = $('<div id="help-dialog"></div>')
		.html('')
		.dialog({
			autoOpen: false,
			title: 'Help',
            width: '600px'
		});
        $("a.help").each(
            function() {
        var url = $(this).attr("href") + " div.document";
        var button = $("<button>.</button>");
        button.button({
            icons: {
                primary: "ui-icon-help"
            },
            text: false
            }).click(
            function (){
                $("#help-dialog").load(url);
                dialog.dialog("open");
            }
        );
        $(this).replaceWith(button);
        });
    }
    
 );
