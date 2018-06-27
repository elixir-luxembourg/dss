$(document).ready(function () {
    $('[data-toggle="popover"]').popover();
    $('.elx-select').select2({
        search: true
    });
    $('.elx-multi-select').select2({
        columns: 2,
        search: true,
        selectAll: true,
        texts: {
            placeholder: 'Select one or more Roles',
        }
    });
});