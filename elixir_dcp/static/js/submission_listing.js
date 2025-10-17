$(document).ready(function () {


    $("#submission_list_table").on('click', 'a[name="button_submission_listing_view"]', function () {
        $.ajax({
            url: $(this).attr('data-url'),
            type: "get",
            success: function (result) {
                $("#submission_view_modal_body").html(result);
                let modal = new bootstrap.Modal(document.getElementById('submission_view_modal'));
                modal.show();
            },
            error: function () {
                alert('An error occurred while loading the Submission Preview section of this page');
            }
        });
    });

    $("#submission_list_table").on('click','a[name="button_submission_listing_delete"]', function () {
        let endpoint = $(this).attr('data-url');
        confirmDialog("delete submission").done(function() {
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
        let endpoint = $(this).attr('data-url');

        $.ajax({
            url: endpoint,
            type: "get",
            success: function (result) {
                $("#submission_share_modal_body").html(result);
                $('.elx-multi-select').select2({
                    theme: 'bootstrap-5',
                    columns: 2,
                    search: true,
                    selectAll: true,
                    texts: {
                        placeholder: 'Select one or more Users',
                    }
                });
                let modal = new bootstrap.Modal(document.getElementById('submission_share_modal'));
                modal.show();
            },
            error: function () {
                alert('An error occurred while loading the Submission Share section of this page');
            }
        });
    });

});