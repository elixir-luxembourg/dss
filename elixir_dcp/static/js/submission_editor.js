$(document).ready(function () {

    $(".elx-date").datepicker({ dateFormat: 'dd/mm/yy' });

    $('select[multiple]').multiselect({
        columns  : 2,
        search   : true,
        selectAll: true,
        texts    : {
            placeholder: 'Select one or more Studies',
        }
    });

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
    /**
     * Contacts Inline Editor button handlers.
     */


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
                refresh_contacts_list();
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

    /**
     * Attachments Inline Editor button handlers.
     */

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
                refresh_attachments_list();
                $("#attachments_inline_editor").html(xhr.responseText);
            }
        });
    });
    /**
     * DISH Inline Editor button handlers.
     */

    function refresh_dishes_list(){
        $.ajax({
            url: $("#dishes_inline_list").attr('data-url'),
            type: "get",
            success: function (result) {
                $("#dishes_inline_list").html(result);
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
                refresh_dishes_list();
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

    /**
     * Data Use Condition Inline Editor button handlers.
     */
    function refresh_ducs_list(){
        $.ajax({
            url: $("#ducs_inline_list").attr('data-url'),
            type: "get",
            success: function (result) {
                $("#ducs_inline_list").html(result);
            },
            error: function () {
                alert('An error occurred while loading the Use Conditions section of this page');
            }
        });
    }

    $("#ducs_inline_editor").on('click', 'a#submission_duc_save', function() {

        var id = $('#form_submission_duc').find( "#id" ).val();
        var base_url  = $('#ducs_inline_editor').attr('data-url');
        $.ajax({
            url: "".concat(base_url, (id.length>0)? "/"+id :""),
            type: 'post',
            data : $('#form_submission_duc').serialize(),
            success: function(result){
                refresh_ducs_list();
                $("#ducs_inline_editor").html(result);

            },
            error: function (xhr, status, error) {
                refresh_ducs_list();
                $("#ducs_inline_editor").html(xhr.responseText);
            }
        });
    });

    $("#ducs_inline_list").on('click', 'a#submission_duc_listing_delete', function() {
        $.ajax({
            url: $(this).attr('data-url'),
            type: "delete",
            success: refresh_ducs_list,
            error: refresh_ducs_list
        });
    });



    $("#ducs_inline_list").on('click', 'a#submission_duc_listing_edit', function() {
        $.ajax({
            url: $(this).attr('data-url'),
            type: "get",
            success: function(result){
                $("#ducs_inline_editor").html(result);
            },
            error: function () {
                alert('An error occurred while loading the selected data use condition group');
            }
        });
    });

    $("div[data-toggle=fieldset]").each(function() {
        var $this = $(this);

        //Add new entry
        $this.find("button[data-toggle=fieldset-add-row]").click(function() {
            var target = $($(this).data("target"))
            console.log(target);
            var oldrow = target.find("[data-toggle=fieldset-entry]:last");
            var row = oldrow.clone(true, true);
            console.log(row.find(":input")[0]);
            var elem_id = row.find(":input")[0].id;
            var elem_num = parseInt(elem_id.replace(/.*-(\d{1,4})-.*/m, '$1')) + 1;
            row.attr('data-id', elem_num);
            row.find(":input").each(function() {
                console.log(this);
                var id = $(this).attr('id').replace('-' + (elem_num - 1) + '-', '-' + (elem_num) + '-');
                $(this).attr('name', id).attr('id', id).val('').removeAttr("checked");
            });
            oldrow.after(row);
        }); //End add new entry

        //Remove row
        $this.find("button[data-toggle=fieldset-remove-row]").click(function() {
            if($this.find("[data-toggle=fieldset-entry]").length > 1) {
                var thisRow = $(this).closest("[data-toggle=fieldset-entry]");
                thisRow.remove();
            }
        }); //End remove row
    });
});