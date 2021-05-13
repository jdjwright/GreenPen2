
$('#id_syllabus-tree').bind('loaded.jstree', function(e, data) {
    $('.select2-hidden-accessible').each(function() {
        $(this).on('select2:select', function (e) {
            console.log(e.params.data.id + " added");
            if(isNaN( points_added[e.params.data.id])) {
                points_added[e.params.data.id] = 1
            }
            else {
                points_added[e.params.data.id] = points_added[e.params.data.id] + 1;
            }
            console.log(points_added)
            set_tree_inserted_syllabus_points()

        })
        $(this).on('select2:unselect', function (e) {

            console.log(e.params.data.id + " removed");
            if(points_added[e.params.data.id] == 1) {
                delete(points_added[e.params.data.id])
            }
            else {
                points_added[e.params.data.id] = points_added[e.params.data.id] - 1;
            }
            console.log(points_added)
            set_tree_inserted_syllabus_points()

        })
    });
})

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

