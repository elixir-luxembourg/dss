function resetTimeOut(){
    window.setTimeout(function() {
        $(".alert").fadeTo(1000, 0).slideUp(1000, function(){
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



$(document).ready(function () {

    var VALIDATION_ERROR = "BAD REQUEST";


    function scroll_to_top(){
        $("html, body").animate({ scrollTop: 0 }, "slow");
        return false;

    }
    function bind_widgets() {

        $('[data-toggle="popover"]').popover();
        $(".elx-date").datepicker({dateFormat: 'dd/mm/yy'});

        $('.elx-select').select2({
            minimumResultsForSearch: -1
        });
        $('.elx-multi-select').select2({
            columns: 2,
            search: true,
            selectAll: true
        });
        $.ajax({
            url: '/autocomplete_institutes'
        }).done(function (data) {
            $('.elx-autocomp-institution').autocomplete({
                source: data,
                minLength: 2
            });
        });


        $("div[data-toggle=fieldset]").each(function () {
            var $this = $(this);
            //Add new entry
            $this.find("button[data-toggle=fieldset-add-row]").click(function () {
                var target = $($(this).data("target"))
                console.log(target);
                var oldrow = target.find("[data-toggle=fieldset-entry]:last");
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


    function refresh_bean_list(bean_name) {

        var bean_label = $("div[id='tabs']").find("a[href='#" + bean_name + "']").text();

        $.ajax({
            url: $("#" + bean_name + "_inline_list").attr('data-url'),
            type: "get",
            success: function (result) {
                $("#" + bean_name + "_inline_list").html(result);
            },
            error: function () {
                alert('An error occurred while loading the ' + bean_label + ' section of this page');
            }
        });
    }

    function bean_list_delete_handler(data_url, bean_name) {
        $.ajax({
            url: data_url,
            type: "delete",
            success: function () {
                refresh_bean_list(bean_name);
            },
            error: function () {
                alert('An error occurred during deletion');
            }
        });
    }


    $("#submission_commands_bar").on('click', 'a[name="button_submission_editor_steer"]', function () {
        var endpoint = $(this).attr('data-url');
        confirmDialog("steer this Submission to next state").done(function () {
            $("#submission-command-dialog").attr("disabled", true);
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
            $("#submission-command-dialog").attr("disabled", true);
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

    function confirmDialog(msg) {
        $("#submission-dialog-text").text(msg);
        var def = $.Deferred();
        $("#submission-command-dialog").dialog({
            autoOpen: true,
            hide: true,
            resizable: false,
            height: 200,
            width: 250,
            modal: true,
            dialogClass: "alert",
            buttons: {
                'Continue': function () {
                    def.resolve();
                    $(this).dialog("close");
                },
                'Cancel': function () {
                    def.reject();
                    $(this).dialog("close");
                }
            }
        });
        return def.promise();
    }

    /**
     *
     *
     * Contacts Inline Editor button handlers.
     *
     *
     */


    $("#contacts_inline_editor").on('click', 'a#submission_contact_save', function () {

        $.ajax({
            url: $('#form_submission_contact').attr('data-url'),
            type: 'post',
            data: $('#form_submission_contact').serialize(),
            success: function (result) {
                refresh_bean_list("contacts");
                $("#contacts_inline_editor").html(result);
                displayInlineSuccess("Submission Contact saved");
                bind_widgets();
                scroll_to_top();
            },
            error: function (xhr, status, error) {
                if (error === VALIDATION_ERROR) {
                    refresh_bean_list("contacts");
                    $("#contacts_inline_editor").html(xhr.responseText);
                    displayInlineError("Please check the validity of your input in highlighted places");
                }
            }

        });
    });
    $("#contacts_inline_list").on('click', 'a#submission_contact_listing_delete', function () {
        bean_list_delete_handler($(this).attr('data-url'), "contacts");
        displayInlineSuccess("Submission Contact deleted.");
    });

    $("#contacts_inline_list").on('click', 'a#submission_contact_listing_edit', function () {
        $.ajax({
            url: $(this).attr('data-url'),
            type: "get",
            success: function (result) {
                $("#contacts_inline_editor").html(result);
                bind_widgets();
            },
            error: function () {
                alert('An error occurred while loading the selected contact');
            }
        });
    });

    /**
     *
     *
     *
     * Attachments Inline Editor button handlers.
     *
     *
     *
     */

    $("#attachments_inline_list").on('click', 'a#submission_attachment_listing_delete', function () {
        bean_list_delete_handler($(this).attr('data-url'), "attachments");
        displayInlineSuccess("Attachment deleted.");
    });

    $("#attachments_inline_editor").on('click', 'a#submission_attachment_add', function () {

        var formData = new FormData($("#form_submission_attachment")[0]);
        $.ajax({
            url: $('#form_submission_attachment').attr('data-url'),
            type: 'post',
            cache: false,
            contentType: false,
            processData: false,
            enctype: 'multipart/form-data',
            data: formData,
            success: function (result) {
                refresh_bean_list("attachments");
                $("#attachments_inline_editor").html(result);
                displayInlineSuccess("Attachment saved");
                scroll_to_top();
            },
            error: function (xhr, status, error) {
                if (error === VALIDATION_ERROR) {
                    refresh_bean_list("attachments");
                    $("#attachments_inline_editor").html(xhr.responseText);
                    displayInlineError("Please check the validity of your input in highlighted places");
                }
            }
        });
    });

    /**
     *
     *
     *
     * DISH Inline Editor button handlers.
     *
     *
     *
     *
     */


    $("#dishes_inline_editor").on('click', 'a#submission_dish_save', function () {

        $.ajax({
            url: $('#form_submission_dish').attr('data-url'),
            type: 'post',
            data: $('#form_submission_dish').serialize(),
            success: function (result) {
                refresh_bean_list("dishes");
                $("#dishes_inline_editor").html(result);
                displayInlineSuccess("Study saved");
                bind_widgets();
                scroll_to_top();
            },
            error: function (xhr, status, error) {
                if (error === VALIDATION_ERROR) {
                    refresh_bean_list("dishes");
                    $("#dishes_inline_editor").html(xhr.responseText);
                    displayInlineError("Please check the validity of your input in highlighted places");
                    bind_widgets();
                }
            }
        });
    });

    $("#dishes_inline_list").on('click', 'a#submission_dish_listing_delete', function () {
        bean_list_delete_handler($(this).attr('data-url'), "dishes");
        displayInlineSuccess("Study deleted");
    });


    $("#dishes_inline_list").on('click', 'a#submission_dish_listing_edit', function () {
        $.ajax({
            url: $(this).attr('data-url'),
            type: "get",
            success: function (result) {
                $("#dishes_inline_editor").html(result);
                bind_widgets();
            },
            error: function () {
                alert('An error occurred while loading the selected study information');
            }
        });
    });


    /**
     *
     *
     *
     *
     * Data Upload Info Inline Editor button handlers.
     *
     *
     *
     *
     */

    $("#uploadinfos_inline_editor").on('click', 'a#submission_uploadinfo_save', function () {

        $.ajax({
            url: $('#form_submission_uploadinfo').attr('data-url'),
            type: 'post',
            data: $('#form_submission_uploadinfo').serialize(),
            success: function (result) {
                refresh_bean_list("uploadinfos");
                $("#uploadinfos_inline_editor").html(result);
                displayInlineSuccess("Upload Checksum saved");
                scroll_to_top();
            },
            error: function (xhr, status, error) {
                if (error === VALIDATION_ERROR) {
                    refresh_bean_list("uploadinfos");
                    $("#uploadinfos_inline_editor").html(xhr.responseText);
                    displayInlineError("Please check the validity of your input in highlighted places");
                    bind_widgets();
                }
            }
        });
    });

    $("#uploadinfos_inline_list").on('click', 'a#submission_uploadinfo_listing_delete', function () {
        bean_list_delete_handler($(this).attr('data-url'), "uploadinfos");
        displayInlineSuccess("Upload Checksum deleted");
    });

    $("#uploadinfos_inline_list").on('click', 'a#submission_uploadinfo_listing_edit', function () {
        $.ajax({
            url: $(this).attr('data-url'),
            type: "get",
            success: function (result) {
                $("#uploadinfos_inline_editor").html(result);
            },
            error: function (xhr, status, error) {
                alert('An error occurred while loading the selected upload information!');
            }
        });
    });


    bind_widgets();

});