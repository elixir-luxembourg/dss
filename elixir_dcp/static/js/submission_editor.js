$(document).ready(function () {


    function bind_widgets(){

        $(".elx-date").datepicker({ dateFormat: 'dd/mm/yy' });

        $('.elx-select').select2({
            minimumResultsForSearch: -1
        });

        $('.elx-select-readonly').select2({
            readonly: true
        });


        /*       $('select[multiple]').multiselect({
                    columns  : 2,
                    search   : true,
                    selectAll: true,
                    texts    : {
                        placeholder: 'Select one or more Studies',
                    }
                });*/
    }
    function bind_duc_tab_widgets() {

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
    }


    $(function () {
        $("#tabs").tabs();

    });


    function refresh_bean_list(bean_name){

        var bean_label = $("div[id='tabs']").find("a[href='#" + bean_name+"']").text();

        $.ajax({
            url: $("#" + bean_name + "_inline_list").attr('data-url'),
            type: "get",
            success: function (result) {
                $("#"+ bean_name + "_inline_list").html(result);
            },
            error: function () {
                alert('An error occurred while loading the ' + bean_label + ' section of this page');
            }
        });
    }

    function bean_list_delete_handler(data_url, bean_name){
        $.ajax({
            url: data_url,
            type: "delete",
            success: function () {
                refresh_bean_list(bean_name);
            },
            error: function () {
                alert('An error occurred during delete');
            }
        });
    }

    /**
     *
     *
     * Contacts Inline Editor button handlers.
     *
     *
     */


    $("#contacts_inline_editor").on('click', 'a#submission_contact_save', function() {

        var id = $('#form_submission_contact').find( "#id" ).val();
        var base_url  = $('#contacts_inline_editor').attr('data-url');
        $.ajax({
            url: "".concat(base_url, (id.length>0)? "/"+id :""),
            type: 'post',
            data : $('#form_submission_contact').serialize(),
            success: function(result){
                refresh_bean_list("contacts");
                $("#contacts_inline_editor").html(result);
                bind_widgets();
            },
            error: function (xhr, status, error) {
                refresh_bean_list("contacts");
                $("#contacts_inline_editor").html(xhr.responseText);
            }
        });
    });
    $("#contacts_inline_list").on('click', 'a#submission_contact_listing_delete', function() {
        bean_list_delete_handler($(this).attr('data-url'), "contacts");
    });

    $("#contacts_inline_list").on('click', 'a#submission_contact_listing_edit', function() {
        $.ajax({
            url: $(this).attr('data-url'),
            type: "get",
            success: function(result){
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

    $("#attachments_inline_list").on('click', 'a#submission_attachment_listing_delete', function() {
        bean_list_delete_handler($(this).attr('data-url'), "attachments");
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
                refresh_bean_list("attachments");
                $("#attachments_inline_editor").html(result);
            },
            error: function (xhr, status, error) {
                refresh_bean_list("attachments");
                $("#attachments_inline_editor").html(xhr.responseText);
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


    $("#dishes_inline_editor").on('click', 'a#submission_dish_save', function() {

        var id = $('#form_submission_dish').find( "#id" ).val();
        var base_url  = $('#dishes_inline_editor').attr('data-url');
        $.ajax({
            url: "".concat(base_url, (id.length>0)? "/"+id :""),
            type: 'post',
            data : $('#form_submission_dish').serialize(),
            success: function(result){
                refresh_bean_list("dishes");
                $("#dishes_inline_editor").html(result);
                bind_widgets();
            },
            error: function (xhr, status, error) {
                refresh_bean_list("dishes");
                $("#dishes_inline_editor").html(xhr.responseText);
                bind_widgets();
            }
        });
    });

    $("#dishes_inline_list").on('click', 'a#submission_dish_listing_delete', function() {
        bean_list_delete_handler($(this).attr('data-url'), "dishes");
    });


    $("#dishes_inline_list").on('click', 'a#submission_dish_listing_edit', function() {
        $.ajax({
            url: $(this).attr('data-url'),
            type: "get",
            success: function(result){
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
     * Data Use Condition Inline Editor button handlers.
     *
     *
     *
     *
     */


    $("#ducs_inline_editor").on('click', 'a#submission_duc_save', function() {

        var id = $('#form_submission_duc').find( "#id" ).val();
        var base_url  = $('#ducs_inline_editor').attr('data-url');
        $.ajax({
            url: "".concat(base_url, (id.length>0)? "/"+id :""),
            type: 'post',
            data : $('#form_submission_duc').serialize(),
            success: function(result){
                refresh_bean_list("ducs");
                $("#ducs_inline_editor").html(result);
                bind_duc_tab_widgets();
            },
            error: function (xhr, status, error) {
                refresh_bean_list("ducs");
                //TODO check the type of error here,
                //only in csae of validation errors we should update the html
                $("#ducs_inline_editor").html(xhr.responseText);
                bind_widgets();
            }
        });
    });

    $("#ducs_inline_list").on('click', 'a#submission_duc_listing_delete', function() {
        bean_list_delete_handler($(this).attr('data-url'), "ducs");
    });

    $("#ducs_inline_list").on('click', 'a#submission_duc_listing_edit', function() {

        $.ajax({
            url: $(this).attr('data-url'),
            type: "get",
            success: function(result){
                $("#ducs_inline_editor").html(result);
                bind_duc_tab_widgets();
            },
            error: function () {
                alert('An error occurred while loading the selected data use condition group');
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

    $("#uploadinfos_inline_editor").on('click', 'a#submission_uploadinfo_save', function() {

        var id = $('#form_submission_uploadinfo').find( "#id" ).val();
        var base_url  = $('#uploadinfos_inline_editor').attr('data-url');
        $.ajax({
            url: "".concat(base_url, (id.length>0)? "/"+id :""),
            type: 'post',
            data : $('#form_submission_uploadinfo').serialize(),
            success: function(result){
                refresh_bean_list("uploadinfos");
                $("#uploadinfos_inline_editor").html(result);
            },
            error: function (xhr, status, error) {
                refresh_bean_list("uploadinfos");
                //TODO check the type of error here,
                //only in csae of validation errors we should update the html
                $("#uploadinfos_inline_editor").html(xhr.responseText);
                bind_widgets();
            }
        });
    });

    $("#uploadinfos_inline_list").on('click', 'a#submission_uploadinfo_listing_delete', function() {
        bean_list_delete_handler($(this).attr('data-url'), "uploadinfos");
    });

    $("#uploadinfos_inline_list").on('click', 'a#submission_uploadinfo_listing_edit', function() {
        alert($(this).attr('data-url'));
        $.ajax({
            url: $(this).attr('data-url'),
            type: "get",
            success: function(result){
                $("#uploadinfos_inline_editor").html(result);
            },
            error: function (xhr, status, error) {
               // alert(error);
                alert('An error occurred while loading the selected upload information!');
            }
        });
    });



    bind_duc_tab_widgets();
    bind_widgets();
});