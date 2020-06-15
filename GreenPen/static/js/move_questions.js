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

$(".insert-button").click(function() {
    let empty_q = $("#empty-question");
    let form_idx = $('#id_question_set-TOTAL_FORMS').val();
    let current_q = $(this).closest($('.question'));
    let current_order_box = current_q.find('.exam-order input');
    let newq = empty_q.clone(true).insertAfter(current_q);
    newq.html().replace(/__prefix__/g, form_idx);
    let debug = newq.html();
    let debug1 = newq.html().replace(/__prefix__/g, form_idx);
    newq.html(debug1);
    newq.removeClass('empty-question').addClass('question');

    $('#id_question_set-TOTAL_FORMS').val(parseInt(form_idx) + 1);

    let new_order_box = newq.find($('.exam-order input'));
    new_order_box.val(Number(current_order_box.val()) +1);
    newq.nextUntil($('#empty-question')).each(function() {
        let order_box = $(this).find('.exam-order input');
        order_box.val(Number(order_box.val())+1);
    })
});

$(".delete-button").click(function(){
    let current_q = $(this).closest($('.question'));
    current_q.find('.exam-delete input').prop('checked', true);
    current_q.nextUntil($('#empty-question')).each(function() {
        let order_box = $(this).find('.exam-order input');
        order_box.val(Number(order_box.val())-1);
    })
    current_q.addClass('deleted-question')
})