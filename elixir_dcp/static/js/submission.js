$(document).ready(function () {

    $("#created").datepicker();




    $(function () {
        if ($("#tabs").attr('page-mode') == 'create')
        {
            $("#tabs").tabs( { disabled: [1, 2] } );

        }else{
            $("#tabs").tabs();
        }
    });

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

    function getSubmissionAttachments(){
        $.ajax({
            url: $("#attachments").attr('data-url'),
            type: "get",
            success: function (result) {
                $("#attachments").html(result);
            },
            error: function () {
                alert('An error occurred while loading the Attachments section of this page');
            }
        });
    }

    $("#attachments").on('click', 'a#submission_attachment_listing_delete', function() {
        $.ajax({
            url: $(this).attr('data-url'),
            type: "delete",
            success: getSubmissionAttachments,
            error: function () {
                alert('An error occurred while deleting Attachment');
            }
        });
    });

    $("#attachments").on('click', 'a#submission_attachment_add', function() {

        var files= $("#file-select")[0].files;

        var formData = new FormData($("#form_submission_attachment")[0]);
        for (var i = 0; i < files.length; i++) {
            var file = files[i];
            console.log(file.name);

            // Add the file to the request.
            formData.append('attachments[]', file, file.name);
        }

        $.ajax({
            url: $('#form_submission_attachment').attr('data-url'),
            type: 'post',
            cache: false,
            contentType: false,
            processData: false,
            enctype: 'multipart/form-data',
            data : formData,
            success: getSubmissionAttachments,
            error: getSubmissionAttachments
        });
    });

    getSubmissionContacts();
    getSubmissionAttachments();
});