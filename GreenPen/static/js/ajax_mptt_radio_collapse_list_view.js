var toggler = document.getElementsByClassName("caret");
var i;

for (i = 0; i < toggler.length; i++) {
  toggler[i].addEventListener("click", function() {

    var url = $('#mistake-children-url').value
    $(this).siblings().filter('ul')[0].classList.toggle("nested");
    this.classList.toggle("caret-down");
  });
}

