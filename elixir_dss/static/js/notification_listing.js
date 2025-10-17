$(document).ready(function () {

    $("#notification_list_table").on('click', 'a[name="button_notification_listing_send"]', function () {
        let endpoint = $(this).attr('data-url');
        confirmDialog("re-send notification").done(function() {
            $.ajax({
                url: endpoint,
                type: "get",
                success: function(result){
                    location.reload()
                },
                error: function (xhr, status, error) {
                    location.reload()
                }
            });

        });
    });

});