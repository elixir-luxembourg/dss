function resetTimeOut() {
    window.setTimeout(function () {
        $(".alert").fadeTo(1000, 0).slideUp(1000, function () {
            let alertElement = document.querySelector(".alert-dismissible");
            if (alertElement) {
                let alert = bootstrap.Alert.getInstance(alertElement);
                if (alert) {
                    alert.close();
                }
            }
        });
    }, 6000);
}

function displayInlineError(msg) {
    $(".inline-editor-messages").prepend('<div class="alert alert-dismissible alert-danger" role="alert"><button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button> <strong>' + msg + '</strong> </div>');
    resetTimeOut();
}

function displayInlineSuccess(msg) {
    $(".inline-editor-messages").prepend('<div class="alert alert-dismissible alert-success" role="alert"><button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button> <strong>' + msg + '</strong> </div>');
    resetTimeOut();
}

$(document).ajaxStart(function () {
    $('body').addClass('wait');
}).ajaxComplete(function () {
    $('body').removeClass('wait');
});

$(document).ready(function () {

    let VALIDATION_ERROR = "BAD REQUEST";

    function bind_widgets() {
        $(".elx-date").datepicker({dateFormat: 'dd/mm/yy'});

        $('.elx-select').select2({
            minimumResultsForSearch: -1
        });

        $('.elx-multi-select').select2({
            columns: 2,
            search: true,
            selectAll: true
        });

        $("div[data-toggle=fieldset]").each(function () {
            let $this = $(this);

            $this.find("button[data-toggle=fieldset-add-row]").click(function () {
                let target = $($(this).data("target"));
                console.log(target);
                let oldrow = target.find("[data-toggle=fieldset-entry]:last");
                let row = oldrow.clone(true, true);
                console.log(row.find(":input")[0]);
                let elem_id = row.find(":input")[0].id;
                let elem_num = parseInt(elem_id.replace(/.*-(\d{1,4})-.*/m, '$1')) + 1;
                row.attr('data-id', elem_num);
                row.find(":input").each(function () {
                    console.log(this);
                    let id = $(this).attr('id').replace('-' + (elem_num - 1) + '-', '-' + (elem_num) + '-');
                    $(this).attr('name', id).attr('id', id).val('').removeAttr("checked");
                });

                oldrow.after(row);
            });

            $this.find("button[data-toggle=fieldset-remove-row]").click(function () {
                if ($this.find("[data-toggle=fieldset-entry]").length > 1) {
                    let thisRow = $(this).closest("[data-toggle=fieldset-entry]");
                    thisRow.remove();
                }
            });
        });
    }

    $("#submission_commands_bar").on('click', 'a[name="button_submission_editor_steer"]', function () {
        let endpoint = $(this).attr('data-url');
        let res = confirmDialog("steer this Submission to next state").done(function () {
            $.ajax({
                url: endpoint,
                type: "get",
                success: function (result) {
                    location.reload()
                },
                error: function (xhr, status, error) {
                    location.reload()
                }
            });
        });
    });

    $("#submission_commands_bar").on('click', 'a[name="button_submission_editor_revert"]', function () {
        let endpoint = $(this).attr('data-url');
        let res = confirmDialog("revert this Submission to its previous state").done(function () {
            $.ajax({
                url: endpoint,
                type: "get",
                success: function (result) {
                    location.reload()
                },
                error: function (xhr, status, error) {
                    location.reload()
                }
            });
        });
    });

    $("#inline_form_container").on('click', 'a#submission_attachment_add', function () {
        let formData = new FormData($("#form_inline_bean")[0]);
        $.ajax({
            url: $('#form_inline_bean').attr('data-url'),
            type: 'post',
            cache: false,
            contentType: false,
            processData: false,
            enctype: 'multipart/form-data',
            data: formData,
            success: function (result) {
                location.reload()
            },
            error: function (xhr, status, error) {
                if (error === VALIDATION_ERROR) {
                    refresh_bean_list("attachments");
                    $("#inline_form_container").html(xhr.responseText);
                    displayInlineError("Please check the validity of your input in highlighted places");
                }
            }
        });
    });

    bind_widgets();
});