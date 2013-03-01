$(
	function(){
		$("span.expand").click(function (){
			var block = $(this).parent().parent();
			var childarray = block.children("div");
			block.toggleClass("open");
			var list = childarray;
			list.toggleClass("hidden");
		});
	}
);
