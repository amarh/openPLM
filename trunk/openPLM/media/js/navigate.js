$(document).ready(function(){

  // Supprime la scrollbar en JS
  $('#Navigate').css('overflow', 'hidden');

  // Insert les images de navigation
//    $('#Navigate')
//    .append('<div id="imgManagement"><span class="imgManagement" id="topControl"></span><span class="imgManagement" id="leftControl"></span><span class="imgManagement" id="rightControl"></span><span class="imgManagement" id="bottomControl"></span></div>');

  // crée un écouteur pour l'évènement de type clic sur les div qui ont l' id #rightControl
  $('#rightControl')
    .bind('click', function(){
      // Move slideInner using left attribute for position
      $('#DivNav').animate({
        "left": "-=100px"
      }, "fast");
    });
    
  // crée un écouteur pour l'évènement de type clic sur les div qui ont l' id #leftControl
  $('#leftControl')
    .bind('click', function(){
      // Move slideInner using left attribute for position
      $('#DivNav').animate({
        "left": "+=100px"
      }, "fast");
    });

  // crée un écouteur pour l'évènement de type clic sur les div qui ont l' id #topControl
  $('#topControl')
    .bind('click', function(){
      // Move slideInner using top attribute for position
      $('#DivNav').animate({
        "top": "+=100px"
      }, "fast");
    });

  // crée un écouteur pour l'évènement de type clic sur les div qui ont l' id #bottomControl
  $('#bottomControl')
    .bind('click', function(){
      // Move slideInner using left attribute for position
      $('#DivNav').animate({
        "top": "-=100px"
      }, "fast");
    });

  $("#DivNav").draggable({
      cursor: 'crosshair'
      });

  });
