let csrftoken = $('meta[name=csrf-token]').attr('content');

function confirmDialog(msg) {
    $("#common-command-dialog").text("You are about to "+ msg);
    let def = $.Deferred();
    $("#common-command-dialog").dialog({
        resizable: false,
        modal: true,
        buttons: {
            'Continue': function() {
                def.resolve();
                $( this ).dialog( "close" );
            },
            'Cancel': function() {
                def.reject();
                $( this ).dialog( "close" );
            }
        },
        close: function() {
            $(this).remove();
        }
    });
    return def.promise();
}
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
            let form = $('<form>');
            form.attr("method", "post");
            form.attr("action", location);

            $.each(args, function (key, value) {
                let field = $('<input>');

                field.attr("type", "hidden");
                field.attr("name", key);
                field.attr("value", value);

                form.append(field);
            });
            let field = $('<input type="hidden" name="csrf_token">').attr('value', csrftoken);
            form.append(field);
            $(form).appendTo('body').submit();
        }
    });

window.setTimeout(function() {
    $(".alert").fadeTo(1000, 0).slideUp(1000, function(){
        let alertElement = document.querySelector(".alert-dismissible");
        if (alertElement) {
            let alert = bootstrap.Alert.getInstance(alertElement);
            if (alert) {
                alert.close();
            }
        }
    });
}, 6000);

$(document).ready(function () {
    document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(function(el) {
        new bootstrap.Tooltip(el);
    });

    $('#query').change(function () {
        $('#sort_by').val('');
    });

    document.querySelectorAll('.start-collapsed').forEach(function(el) {
        let collapse = new bootstrap.Collapse(el, { toggle: false });
        collapse.hide();
    });
    document.querySelectorAll('.start-visible').forEach(function(el) {
        let collapse = new bootstrap.Collapse(el, { toggle: false });
        collapse.show();
    });

    $('table.datatable').dataTable();
});
