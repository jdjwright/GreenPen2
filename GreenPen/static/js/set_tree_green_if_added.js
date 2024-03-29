
$('#id_syllabus-tree').bind('loaded.jstree', function (e, data) {
    bind_select2_to_tree()
})

function bind_select2_to_tree() {
    $('.select2-hidden-accessible').not('.syllabus-tree-bound').each(function() {
        $(this).on('select2:select', function (e) {
            if(isNaN( points_added[e.params.data.id])) {
                points_added[e.params.data.id] = 1
            }
            else {
                points_added[e.params.data.id] = points_added[e.params.data.id] + 1;
            }
            set_tree_inserted_syllabus_points()

        })
        $(this).on('select2:unselect', function (e) {

            if(points_added[e.params.data.id] == 1) {
                delete(points_added[e.params.data.id])
            }
            else {
                points_added[e.params.data.id] = points_added[e.params.data.id] - 1;
            }
            set_tree_inserted_syllabus_points()

        })
        $(this).addClass('syllabus-tree-bound');

        // Remove the keyup binding so we don't keep firing events.

    });
}

$('#id_syllabus-tree').bind('open_node.jstree', function(e, data) {
    set_tree_inserted_syllabus_points()
})

function set_tree_inserted_syllabus_points() {
    $('#id_syllabus-tree').find('*').find('li').each(function() {
        let id = this.id
        if (id in points_added) {
            $(this).addClass('selected_syllabus_point')

        }
        else {
        $(this).removeClass('selected_syllabus_point')
        }

    })
}

