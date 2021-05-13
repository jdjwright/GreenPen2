let options = $('.question-div').find('option')
let points_added = {}


set_initial_points(options)

console.log(points_added)

function set_initial_points(options) {
    options.each(function() {
        if(isNaN( points_added[$(this).val()])) {
            points_added[$(this).val()] = 1
        }
        else {
            points_added[$(this).val()] = points_added[$(this).val()] + 1;
        }
    });
}