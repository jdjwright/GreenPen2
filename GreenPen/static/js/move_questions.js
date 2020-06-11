$(".up-button").click(function() {
    let question_div = $(this).closest($('.question'));
    let order_box = question_div.find($('.exam-order input'));
    let current = order_box.val();
    if(Number(current)===1){
       return
    }

    let previous_div = question_div.prev();
    question_div.insertBefore(previous_div);

    order_box.val(Number(current)-1);
    let swapped_box = previous_div.find($('.exam-order input'));
    current = order_box.val();
    swapped_box.val(Number(current)+1);
});

$(".down-button").click(function() {
    let question_div = $(this).closest($('.question'));
    let order_box = question_div.find($('.exam-order input'));
    let current = order_box.val();
    let max = $('.question').length;

    if(Number(current)===max+1){
        return
    }

    let next = question_div.next();
    question_div.insertAfter(next);

    order_box.val(Number(current)+1);
    let swapped_box = next.find($('.exam-order input'));
    current = order_box.val();
    swapped_box.val(Number(current)-1);
});

$("#add-question").click(function() {
    let empty_q = $("#empty-question");
    let total_qs = $('.question').length;
    let last = $().find()
});