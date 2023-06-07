$(function() {
    $(".lecturer").draggable({
        helper: 'clone'
    });

    $(".course").droppable({
        drop: function(event, ui) {
            let dropped = ui.draggable;
            let droppedOn = $(this);
            let lecturerId = dropped.data('lecturer-id');
            let courseId = droppedOn.data('course-id');

            // AJAX call to Django view to assign lecturer to course
            $.ajax({
                url: '/assign_lecturer/',  // update this to the URL of your Django view
                type: 'post',
                data: {
                    'lecturer_id': lecturerId,
                    'course_id': courseId,
                    'csrfmiddlewaretoken': $('input[name=csrfmiddlewaretoken]').val()
                },
                success: function(response) {
                    if (response.success) {
                        console.log(`Lecturer ${lecturerId} assigned to course ${courseId}`);
                        $(droppedOn).append(dropped.clone());
                    } else {
                        console.log(response.error);
                    }
                }
            });
        }
    });
});
