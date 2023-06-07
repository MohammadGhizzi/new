$(document).ready(function () {
    function displayEventModal(calEvent) {
        $('#eventTitle').val(calEvent.title);
        $('#eventModal').modal('show');

        $('#saveEvent').off('click').on('click', function () {
            calEvent.title = $('#eventTitle').val();

            if (!calEvent.title) {
                alert('Event title cannot be empty.');
                return;
            }

            $('#calendar').fullCalendar('updateEvent', calEvent);

            // AJAX call to update event in the database
            $.ajax({
                url: '/update_event/',
                data: {
                    'event_id': calEvent._id,
                    'title': calEvent.title,
                },
                type: 'post',
                success: function(response) {
                    $('#eventModal').modal('hide');
                },
                error: function(jqXHR, textStatus, errorThrown) {
                    alert('Error: ' + textStatus + ' ' + errorThrown);
                }
            });
        });
    }

    function addNewEvent(date, title, description, color) {
        if (!title || !description || !color) {
            alert('All fields are required.');
            return;
        }

        var newEvent = {
            title: title,
            start: date,
            allDay: true,
            description: description,
            color: color
        };

        // AJAX call to add new event to the database
        $.ajax({
            url: '/add_event/',
            data: {
                'title': newEvent.title,
                'start': newEvent.start,
                'description': newEvent.description,
                'color': newEvent.color,
            },
            type: 'post',
            success: function(response) {
                newEvent._id = response.event_id;
                $('#calendar').fullCalendar('renderEvent', newEvent, true);
            },
            error: function(jqXHR, textStatus, errorThrown) {
                alert('Error: ' + textStatus + ' ' + errorThrown);
            }
        });
    }

    $('#calendar').fullCalendar({
        eventClick: function (calEvent, jsEvent, view) {
            displayEventModal(calEvent);
        }
    });

    $('#calendar').on('contextmenu', '.fc-event', function (e) {
        e.preventDefault();
        var eventElement = $(this);
        var eventObject = eventElement.data('eventObject');

        $.contextMenu({
            selector: eventElement,
            items: {
                addEvent: {
                    name: "Add another event",
                    callback: function () {
                        var title = prompt("Enter event title:");
                        var description = prompt("Enter event description:");
                        var color = prompt("Enter event color (in hex format):");

                        if (title && description && color) {
                            addNewEvent(eventObject.start, title, description, color);
                        }
                    }
                },
                deleteEvent: {
                    name: "Delete event linked to this day",
                    callback: function () {
                        // AJAX call to delete event from the database
                        $.ajax({
                            url: '/delete_event/',
                            data: {
                                'event_id': eventObject._id
                            },
                            type: 'post',
                            success: function(response) {
                                $('#calendar').fullCalendar('removeEvents', eventObject._id);
                            },
                            error: function(jqXHR, textStatus, errorThrown) {
                                alert('Error: ' + textStatus + ' ' + errorThrown);
                            }
                        });
                    }
                },
            }
        });
    });
});
