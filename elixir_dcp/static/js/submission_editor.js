$(document).ready(function () {

    $(".elx-date").datepicker({ dateFormat: 'dd/mm/yy' });

    $(function () {
        $("#tabs").tabs();

    });

    function refresh_contacts_list(){
        $.ajax({
            url: $("#contacts_inline_list").attr('data-url'),
            type: "get",
            success: function (result) {
                $("#contacts_inline_list").html(result);
            },
            error: function () {
                alert('An error occurred while loading the Contacts section of this page');
            }
        });
    }


    $("#contacts_inline_editor").on('click', 'a#submission_contact_save', function() {

        var id = $('#form_submission_contact').find( "#id" ).val();
        var base_url  = $('#contacts_inline_editor').attr('data-url');
        $.ajax({
            url: "".concat(base_url, (id.length>0)? "/"+id :""),
            type: 'post',
            data : $('#form_submission_contact').serialize(),
            success: function(result){
                refresh_contacts_list();
                $("#contacts_inline_editor").html(result);
            },
            error: function (xhr, status, error) {
                $("#contacts_inline_editor").html(xhr.responseText);
            }
        });
    });
    $("#contacts_inline_list").on('click', 'a#submission_contact_listing_delete', function() {
        $.ajax({
            url: $(this).attr('data-url'),
            type: "delete",
            success: refresh_contacts_list,
            error: refresh_contacts_list
        });
    });

    $("#contacts_inline_list").on('click', 'a#submission_contact_listing_edit', function() {
        $.ajax({
            url: $(this).attr('data-url'),
            type: "get",
            success: function(result){
                $("#contacts_inline_editor").html(result);
            },
            error: function () {
                alert('An error occurred while loading the selected contact');
            }
        });
    });

    function refresh_attachments_list(){
        $.ajax({
            url: $("#attachments_inline_list").attr('data-url'),
            type: "get",
            success: function (result) {
                $("#attachments_inline_list").html(result);
            },
            error: function () {
                alert('An error occurred while loading the Attachments section of this page');
            }
        });
    }


    $("#attachments_inline_list").on('click', 'a#submission_attachment_listing_delete', function() {
        $.ajax({
            url: $(this).attr('data-url'),
            type: "delete",
            success: refresh_attachments_list,
            error: function () {
                alert('An error occurred while deleting Attachment');
            }
        });
    });

    $("#attachments_inline_editor").on('click', 'a#submission_attachment_add', function() {

        var formData = new FormData($("#form_submission_attachment")[0]);
        $.ajax({
            url: $('#attachments_inline_editor').attr('data-url'),
            type: 'post',
            cache: false,
            contentType: false,
            processData: false,
            enctype: 'multipart/form-data',
            data : formData,
            success: function(result){
                refresh_attachments_list();
                $("#attachments_inline_editor").html(result);
            },
            error: function (xhr, status, error) {
                $("#attachments_inline_editor").html(xhr.responseText);
            }
        });
    });

    function refresh_dishes_list(){
        $.ajax({
            url: $("#dishes").attr('data-url'),
            type: "get",
            success: function (result) {
                $("#dishes").html(result);
            },
            error: function () {
                alert('An error occurred while loading the Study Info section of this page');
            }
        });
    }

    $("#dishes_inline_editor").on('click', 'a#submission_dish_save', function() {

        var id = $('#form_submission_dish').find( "#id" ).val();
        var base_url  = $('#dishes_inline_editor').attr('data-url');
        $.ajax({
            url: "".concat(base_url, (id.length>0)? "/"+id :""),
            type: 'post',
            data : $('#form_submission_dish').serialize(),
            success: function(result){
                refresh_dishes_list();
                $("#dishes_inline_editor").html(result);
            },
            error: function (xhr, status, error) {
                $("#dishes_inline_editor").html(xhr.responseText);
            }
        });
    });
    $("#dishes_inline_list").on('click', 'a#submission_dish_listing_delete', function() {
        $.ajax({
            url: $(this).attr('data-url'),
            type: "delete",
            success: refresh_dishes_list,
            error: refresh_dishes_list
        });
    });

    $("#dishes_inline_list").on('click', 'a#submission_dish_listing_edit', function() {
        $.ajax({
            url: $(this).attr('data-url'),
            type: "get",
            success: function(result){
                $("#dishes_inline_editor").html(result);
            },
            error: function () {
                alert('An error occurred while loading the selected study information');
            }
        });
    });

});