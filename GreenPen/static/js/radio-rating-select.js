$(document).on('click',".stu-rating1", function() {
    let a = $(this).closest('.rating-selection').find('.rating-input');
    a[0].value = 1
});

$(document).on('click',".stu-rating2", function() {
    let a = $(this).closest('.rating-selection').find('.rating-input');
    a[0].value = 2
});

$(document).on('click',".stu-rating3", function() {
    let a = $(this).closest('.rating-selection').find('.rating-input');
    a[0].value = 3
});

$(document).on('click',".stu-rating4", function() {
    let a = $(this).closest('.rating-selection').find('.rating-input');
    a[0].value = 4
});

$(document).on('click',".stu-rating5", function() {
    let a = $(this).closest('.rating-selection').find('.rating-input');
    a[0].value = 5
});

