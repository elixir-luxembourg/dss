function resetTimeOut() {
    globalThis.setTimeout(function () {
        $(".alert").fadeTo(1000, 0).slideUp(1000, function () {
            let alertElement = document.querySelector(".alert-dismissible");
            if (alertElement) {
                let alert = bootstrap.Alert.getInstance(alertElement);
                if (alert) {
                    alert.close();
                }
            }
        });
    }, 6000);
}

function displayInlineError(msg) {
    $(".inline-editor-messages").prepend('<div class="alert alert-dismissible alert-danger" role="alert"><button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button> <strong>' + msg + '</strong> </div>');
    resetTimeOut();
}

function displayInlineSuccess(msg) {
    $(".inline-editor-messages").prepend('<div class="alert alert-dismissible alert-success" role="alert"><button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button> <strong>' + msg + '</strong> </div>');
    resetTimeOut();
}

function updateFieldsetInputIds(input, oldNum, newNum) {
    let id = $(input).attr('id').replace('-' + oldNum + '-', '-' + newNum + '-');
    $(input).attr('name', id).attr('id', id).val('').removeAttr("checked");
}

$(document).ajaxStart(function () {
    $('body').addClass('wait');
}).ajaxComplete(function () {
    $('body').removeClass('wait');
});

$(document).ready(function () {

    let VALIDATION_ERROR = "BAD REQUEST";

    function bind_widgets() {
        $(".elx-date").datepicker({dateFormat: 'dd/mm/yy'});

        $('.elx-select').select2({
            theme: 'bootstrap-5',
            minimumResultsForSearch: -1
        });

        $('.elx-multi-select').select2({
            theme: 'bootstrap-5',
            columns: 2,
            search: true,
            selectAll: true
        });

        $("div[data-toggle=fieldset]").each(function () {
            let $this = $(this);

            $this.find("button[data-toggle=fieldset-add-row]").click(function () {
                let target = $($(this).data("target"));
                console.log('Target:', target);
                let oldrow = target.find("[data-toggle=fieldset-entry]:last");
                if (oldrow.length === 0) {
                    console.error('No fieldset-entry found to clone');
                    return;
                }
                let row = oldrow.clone(true, true);
                let firstInput = row.find(":input")[0];
                if (!firstInput) {
                    console.error('No input fields found in cloned row');
                    return;
                }
                console.log('First input:', firstInput);
                let elem_id = firstInput.id;
                let elem_num = parseInt(elem_id.replace(/.*-(\d{1,4})-.*/m, '$1')) + 1;
                row.attr('data-id', elem_num);
                row.find(":input").each(function () {
                    updateFieldsetInputIds(this, elem_num - 1, elem_num);
                });

                oldrow.after(row);
            });

            $this.find("button[data-toggle=fieldset-remove-row]").click(function () {
                if ($this.find("[data-toggle=fieldset-entry]").length > 1) {
                    let thisRow = $(this).closest("[data-toggle=fieldset-entry]");
                    thisRow.remove();
                }
            });
        });
    }

    // Listen on document level for proceed/revert buttons (they can be in different locations)
    $(document).on('click', 'a[name="button_submission_editor_steer"]', function () {
        let endpoint = $(this).attr('data-url');
        let res = confirmDialog("steer this Submission to next state").done(function () {
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

    $(document).on('click', 'a[name="button_submission_editor_revert"]', function () {
        let endpoint = $(this).attr('data-url');
        let res = confirmDialog("revert this Submission to its previous state").done(function () {
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

    $("#inline_form_container").on('click', 'a#submission_attachment_add', function () {
        let formData = new FormData($("#form_inline_bean")[0]);
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

    function toggleNotesField(checkboxId, notesFieldId) {
        const checkbox = $('#' + checkboxId);
        const notesField = $('#' + notesFieldId);
        if (checkbox.length && notesField.length) {
            const notesWrapper = notesField.closest('.mb-3');
            function updateVisibility() {
                if (checkbox.is(':checked')) {
                    notesWrapper.show();
                } else {
                    notesWrapper.hide();
                }
            }
            updateVisibility();
            checkbox.on('change', updateVisibility);
        }
    }
    toggleNotesField('restriction_rs', 'restriction_rs_notes');
    toggleNotesField('restriction_gs', 'restriction_gs_notes');
    toggleNotesField('restriction_user_specific', 'restriction_user_specific_notes');
    toggleNotesField('restriction_ts', 'restriction_ts_notes');
    toggleNotesField('restriction_ts_lcsb', 'restriction_ts_lcsb_date');
    toggleNotesField('restriction_pub', 'restriction_pub_notes');
    toggleNotesField('restriction_rtn', 'restriction_rtn_notes');
    toggleNotesField('restriction_us', 'restriction_us_notes');
    toggleNotesField('restriction_ip', 'restriction_ip_notes');
    toggleNotesField('dac_approval_required', 'dac_approval_notes');
    toggleNotesField('has_special_subjects', 'special_subjects_notes');

    function toggleNotesForMultiSelectFields(selectId, notesFieldId, triggerValue) {
        const select = $('#' + selectId);
        const notesField = $('#' + notesFieldId);
        if (select.length && notesField.length) {
            const notesWrapper = notesField.closest('.mb-3');
            function updateVisibility() {
                const selectedValues = select.val() || [];
                if (selectedValues.includes(triggerValue)) {
                    notesWrapper.show();
                } else {
                    notesWrapper.hide();
                }
            }
            updateVisibility();
            select.on('change', updateVisibility);
        }
    }
    toggleNotesForMultiSelectFields('sci_datatypes', 'sci_datatypes_notes', 'Other');
    toggleNotesForMultiSelectFields('gdpr_datatypes', 'gdpr_datatypes_notes', 'other');
    toggleNotesForMultiSelectFields('consent_status_code', 'consent_notes', 'ht');

    // Handle personal data workflow visibility
    function togglePersonalDataFields() {
        const containsPersonalData = $('#contains_personal_data');
        const dataProcessingType = $('#data_processing_type');
        const personalDataFields = $('#personal-data-fields');
        const gdprFields = $('#gdpr-fields');
        
        if (containsPersonalData.length && personalDataFields.length && gdprFields.length) {
            function updateVisibility() {
                if (containsPersonalData.is(':checked')) {
                    personalDataFields.show();
                    
                    // Show GDPR fields only if processing type is pseudonymised or direct_identifiers
                    const processingType = dataProcessingType.val() || '';
                    if (processingType === 'pseudonymised' || processingType === 'direct_identifiers') {
                        gdprFields.show();
                    } else {
                        gdprFields.hide();
                    }
                } else {
                    personalDataFields.hide();
                    gdprFields.hide();
                }
            }
            
            updateVisibility();
            containsPersonalData.on('change', updateVisibility);
            dataProcessingType.on('change', updateVisibility);
        }
    }
    togglePersonalDataFields();

    $('#submission_create_modal').on('shown.bs.modal', function () {
        $(this).find('.elx-select').select2({
            theme: 'bootstrap-5',
            minimumResultsForSearch: -1,
            dropdownParent: $('#submission_create_modal')
        });
    });

    $('#submission_create_modal').on('hidden.bs.modal', function () {
        $(this).find('.elx-select').select2('destroy');
    });



    const checkbox = document.getElementById("responsibilityCheck");
    const confirmBtn = document.getElementById("responsibilityConfirmBtn");

    if (checkbox && confirmBtn) {
        checkbox.addEventListener("change", () => {
            confirmBtn.disabled = !checkbox.checked;
        });

        document.getElementById("responsibilityModal").addEventListener("show.bs.modal", () => {
            checkbox.checked = false;
            confirmBtn.disabled = true;
        });
    }

    const form = document.querySelector('form');
    if (form) {
        form.addEventListener('submit', function (e) {
            const btn = document.getElementById('submit-btn');
            if (!btn) return;
            if (btn.disabled) {
                e.preventDefault();
                return;
            }
            btn.disabled = true;
            btn.innerHTML = '<i class="bi bi-hourglass-split"></i> Saving...';
        });
    }


});