$(document).ready(function () {


    function confirmDialog(msg) {
        $("#submission-dialog-text").text(msg);
        var def = $.Deferred();
        $("#submission-command-dialog").dialog({
            autoOpen: true,
            hide: true,
            resizable: false,
            height: 150,
            modal: true,
            dialogClass: "alert",
            buttons: {
                'Continue': function() {
                    def.resolve();
                    $( this ).dialog( "close" );
                },
                'Cancel': function() {
                    def.reject();
                    $( this ).dialog( "close" );
                }
            }
    });
        return def.promise();
    }

    $("#submission_list_table").on('click', 'a[name="button_submission_listing_view"]', function () {
        $.ajax({
            url: $(this).attr('data-url'),
            type: "get",
            success: function (result) {
                $("#submission_view_modal_body").html(result);
                $("#submission_view_modal").modal('show');
            },
            error: function () {
                alert('An error occurred while loading the Submission Preview section of this page');
            }
        });
    });

    $("#submission_list_table").on('click','a[name="button_submission_listing_delete"]', function () {
        var endpoint = $(this).attr('data-url');
        confirmDialog("delete").done(function() {
            $.ajax({
                url: endpoint,
                type: "delete",
                success: function(result){
                    location.reload()
                },
                error: function (xhr, status, error) {
                    location.reload()
                }
            });

        });
    });

    $("#submission_list_table").on('click', 'a[name="button_submission_listing_share"]', function () {
        var endpoint = $(this).attr('data-url');

        $.ajax({
            url: endpoint,
            type: "get",
            success: function (result) {
                $("#submission_share_modal_body").html(result);
                $('.elx-multi-select').select2({
                    columns: 2,
                    search: true,
                    selectAll: true,
                    texts: {
                        placeholder: 'Select one or more Users',
                    }
                });
                $("#submission_share_modal").modal('show');
            },
            error: function () {
                alert('An error occurred while loading the Submission Share section of this page');
            }
        });
    });

});