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
    let empty_q = $(".empty-question").first().clone(true);
    let current_q = $(this).closest($('.question'));
    let form_idx = $('#id_question_set-TOTAL_FORMS').val();
    let debug_html=empty_q.html();
    let fixed_html = debug_html.replace(/__prefix__/g, form_idx);
    empty_q.html(fixed_html);
    $('#id_question_set-TOTAL_FORMS').val(parseInt(form_idx) + 1);
    empty_q.insertAfter(current_q);
    empty_q.removeClass('empty-question');
    let order_box = empty_q.find('.exam-order input');
    order_box.val(-1)
    empty_q.slideDown();

    set_order()

});

$(document).on('click',".delete-button", function(){
    let current_q = $(this).closest($('.question'));
    current_q.find('.exam-delete input').prop('checked', true);
    current_q.nextUntil($('#empty-question')).each(function() {
        let order_box = $(this).find('.exam-order input');
        // Only change ones with an exiting order, or we'll cause errors:
        if (order_box.val()) {
            order_box.val(Number(order_box.val()) - 1);
        };
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
        let order_box = $(this).find('.exam-order input');
        if(order_box.val()){

            order_box.val(i);
            i++;
            }
    });
}