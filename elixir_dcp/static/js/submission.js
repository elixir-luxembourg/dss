$(document).ready(function () {

    $("#created").datepicker();


    function getSubmissionContacts(){
        $.ajax({
            url: $("#contacts").attr('data-url'),
            type: "get",
            success: function (result) {
                $("#contacts").html(result);
            },
            error: function () {
                alert('An error occurred while loading the Contacts section of this page');
            }
        });
    }

    $(function () {
        if ($("#tabs").attr('page-mode') == 'create')
        {
            $("#tabs").tabs( { disabled: [1] } );

        }else{
            $("#tabs").tabs();
        }
    });

    $("#contacts").on('click', 'a#submission_contact_listing_delete', function() {
        $.ajax({
            url: $(this).attr('data-url'),
            type: "delete",
            success: getSubmissionContacts,
            error: function () {
                alert('An error occurred while deleting Contact');
            }
        });
    });

    $("#contacts").on('click', 'a#submission_contact_add', function() {
        $.ajax({
            url: $('#form_submission_contact').attr('data-url'),
            type: 'post',
            data : $('#form_submission_contact').serialize(),
            success: getSubmissionContacts,
            error: function () {
                alert('An error occurred while adding Contact');
            }
        });
    });


    getSubmissionContacts();
});