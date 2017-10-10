var csrftoken = $('meta[name=csrf-token]').attr('content');

$.ajaxSetup({
    beforeSend: function (xhr, settings) {
        if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken)
        }
    }
});

$.extend(
    {
        redirectPost: function (location, args) {
            var form = $('<form>');
            form.attr("method", "post");
            form.attr("action", location);

            $.each(args, function (key, value) {
                var field = $('<input>');

                field.attr("type", "hidden");
                field.attr("name", key);
                field.attr("value", value);

                form.append(field);
            });
            var field = $('<input type="hidden" name="csrf_token">').attr('value', csrftoken);
            form.append(field);
            $(form).appendTo('body').submit();
        }
    });


$(document).ready(function () {

    $.material.init();
    $('[data-toggle="tooltip"]').tooltip();

    $('#query').change(function () {
        $('#sort_by').val('');
    });
    $('.start-collapsed').collapse('hide');
    $('.start-visible').collapse('show');

})
;