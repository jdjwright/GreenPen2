$(document).on('click',".up-button", function() {
    let question_div = $(this).closest($('.question'));
    let order_box = question_div.find($('.exam-order input'));
    let current = order_box.val();
    if(Number(current)===1){
       return
    }

    let previous_div = question_div.prev();
    question_div.insertBefore(previous_div);
    question_div.slideDown()

    order_box.val(Number(current)-1);
    let swapped_box = previous_div.find($('.exam-order input'));
    current = order_box.val();
    swapped_box.val(Number(current)+1);
});

$(document).on('click',".down-button", function() {
    let question_div = $(this).closest($('.question'));
    let order_box = question_div.find($('.exam-order input'));
    let current = order_box.val();
    let max = $('.question').length;

    if(Number(current)===max+1){
        return
    }

    let next = question_div.next();
    question_div.insertAfter(next);
    question_div.slideDown()

    order_box.val(Number(current)+1);
    let swapped_box = next.find($('.exam-order input'));
    current = order_box.val();
    swapped_box.val(Number(current)-1);
});

$(document).on('click',".insert-button", function() {
    let empty_q = $(".blank-question").first();
    let current_q = $(this).closest($('.question'));
    empty_q.removeClass('blank-question');
    empty_q.insertAfter(current_q);
    empty_q.slideDown();

    set_order()

});

$(document).on('click',".delete-button", function(){
    let current_q = $(this).closest($('.question'));
    current_q.find('.exam-delete input').prop('checked', true);
    current_q.nextUntil($('#empty-question')).each(function() {
        let order_box = $(this).find('.exam-order input');
        order_box.val(Number(order_box.val())-1);
    })
    current_q.addClass('deleted-question')
})

$(document).on('change',".textInput", function(){
    let question = $(this).closest($('.question, .blank-question'));
    question.removeClass('blank-question').addClass('question');
    set_order();

});

function set_order(){
    let i = 1;
    $('.question').each( function(){
        number_box = $(this).find('.textInput');
        if(number_box.val()){
            let order_box = $(this).find('.exam-order input');
            order_box.val(i);
            i++;
            }
    });
}