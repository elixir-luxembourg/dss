function resetTimeOut() {
    window.setTimeout(function () {
        $(".alert").fadeTo(1000, 0).slideUp(1000, function () {
            $(".alert-dismissible").alert('close');
            //$(this).remove();
        });
    }, 6000);
}

function displayInlineError(msg) {
    $(".inline-editor-messages").prepend('<div class="alert alert-dismissible alert-danger" role="alert"><button type="button" class="close" data-dismiss="alert">×</button> <strong>' + msg + '</strong> </div>');
    resetTimeOut();
}

function displayInlineSuccess(msg) {
    $(".inline-editor-messages").prepend('<div class="alert alert-dismissible alert-success" role="alert"><button type="button" class="close" data-dismiss="alert">×</button> <strong>' + msg + '</strong> </div>');
    resetTimeOut();
}


function scroll_to_top() {

    $("html, body").animate({scrollTop: 0}, "slow");

    return false;

}


$(document).ready(function () {

    var VALIDATION_ERROR = "BAD REQUEST";



    $('#form_submission_basics').on('keyup change paste', 'input, select, textarea', function(){
        $('#btn_save_submission_basics').attr('disabled', false);
    });

    $('#btn_save_submission_basics').attr('disabled', true)


    $("#inline_add_new_button").click(function () {
        var endpoint = $(this).attr('data-url');

        $.ajax({
            url: endpoint,
            type: "get",
            success: function (result) {
                $("#inline_form_container").html(result);
                $('#inline_form_container').show();
                bind_widgets();
            },
            error: function () {
                alert('An error occurred while trying to load form to add new records.');
            }
        });
        $("#inline_form_container").show();
    });


    function bind_widgets() {

        /* This is needed for help links */
        $('[data-toggle="popover"]').popover();

        /* A working date selector */
        $(".elx-date").datepicker({dateFormat: 'dd/mm/yy'});

        /* Select2  single selectors */
        $('.elx-select').select2({
            minimumResultsForSearch: -1
        });

        /* Select2 multi selectors */
        $('.elx-multi-select').select2({
            columns: 2,
            search: true,
            selectAll: true
        });

        // $.ajax({
        //     url: '/autocomplete_institutes'
        // }).done(function (data) {
        //     $('.elx-autocomp-institution').autocomplete({
        //         source: data,
        //         minLength: 2
        //     });
        // });

        $("div[data-toggle=fieldset]").each(function () {
            var $this = $(this);

            //Add new entry
            $this.find("button[data-toggle=fieldset-add-row]").click(function () {
                var target = $($(this).data("target"))
                console.log(target);
                var oldrow = target.find("[data-toggle=fieldset-entry]:last");
                oldrow.find(".elx-select").select2('destroy');
                var row = oldrow.clone(true, true);
                console.log(row.find(":input")[0]);
                var elem_id = row.find(":input")[0].id;
                var elem_num = parseInt(elem_id.replace(/.*-(\d{1,4})-.*/m, '$1')) + 1;
                row.attr('data-id', elem_num);
                row.find(":input").each(function () {
                    console.log(this);
                    var id = $(this).attr('id').replace('-' + (elem_num - 1) + '-', '-' + (elem_num) + '-');
                    $(this).attr('name', id).attr('id', id).val('').removeAttr("checked");
                });

                oldrow.after(row);
                oldrow.find(".elx-select").select2({
                    minimumResultsForSearch: -1
                });
                row.find(".elx-select").select2({
                    minimumResultsForSearch: -1
                });
            }); //End add new entry

            //Remove row
            $this.find("button[data-toggle=fieldset-remove-row]").click(function () {
                if ($this.find("[data-toggle=fieldset-entry]").length > 1) {
                    var thisRow = $(this).closest("[data-toggle=fieldset-entry]");
                    thisRow.remove();
                }
            }); //End remove row
        });


    }


    $(function () {
        $("#tabs").tabs();

    });


    $("#submission_commands_bar").on('click', 'a[name="button_submission_editor_steer"]', function () {
        var endpoint = $(this).attr('data-url');

        var res = confirmDialog("steer this Submission to next state").done(function () {
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
        var endpoint = $(this).attr('data-url');
        confirmDialog("revert this Submission to its previous state").done(function () {
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


    /**
     *
     *
     *  Inline Editor common handlers.
     *
     *
     */



    $("#inline_form_container").on('click', 'a#inline_bean_save', function () {

        $.ajax({
            url: $('#form_inline_bean').attr('data-url'),
            type: 'post',
            data: $('#form_inline_bean').serialize(),
            success: function (result) {
                location.reload()

            },
            error: function (xhr, status, error) {
                if (error === VALIDATION_ERROR) {

                    $("#inline_form_container").html(xhr.responseText);
                    displayInlineError("Please check the validity of your input in highlighted places");
                    bind_widgets();
                }
            }

        });
    });

    $("#inline_form_container").on('click', 'a#inline_bean_cancel', function () {

        $("#inline_form_container").html("");
        displayInlineError("Form cancelled");
    });

    $("#inline_columns_container").on('click', 'a#inline_listing_delete', function () {
        delete_endpoint = $(this).attr('data-url');

        $.ajax({
            url: delete_endpoint,
            type: "delete",
            success: function () {
                location.reload()
            },
            error: function () {
                alert('An error occurred during deletion');
            }
        });

    });

    $("#inline_columns_container").on('click', 'a#inline_listing_edit', function () {
        $.ajax({
            url: $(this).attr('data-url'),
            type: "get",
            success: function (result) {
                $("#inline_form_container").html(result);
                $('#inline_form_container').show();
                bind_widgets();

            },
            error: function () {
                alert('An error occurred while loading the selected record');
            }
        });
    });

    /**
     *
     *
     *
     * Attachments Inline Editor save button has a different handler.
     *
     *
     *
     */

    $("#inline_form_container").on('click', 'a#submission_attachment_add', function () {

        var formData = new FormData($("#form_inline_bean")[0]);
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