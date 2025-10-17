let csrftoken = $('meta[name=csrf-token]').attr('content');

function confirmDialog(msg) {
    // Update modal message
    $("#command-dialog-text").text("You are about to " + msg + "!");

    // Create deferred promise
    let def = $.Deferred();

    // Get or create Bootstrap modal instance
    let modalElement = document.getElementById('common-command-dialog');
    let modal = bootstrap.Modal.getInstance(modalElement) || new bootstrap.Modal(modalElement);

    // Handle continue button click
    $('#confirm-dialog-continue').off('click').on('click', function() {
        def.resolve();
        modal.hide();
    });

    // Handle modal dismiss/cancel (reject the promise)
    $(modalElement).off('hidden.bs.modal').on('hidden.bs.modal', function() {
        if (def.state() === 'pending') {
            def.reject();
        }
    });

    // Show the modal
    modal.show();

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
