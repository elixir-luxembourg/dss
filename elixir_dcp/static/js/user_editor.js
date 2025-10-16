$(document).ready(function () {
    document.querySelectorAll('[data-bs-toggle="popover"]').forEach(function(el) {
        new bootstrap.Popover(el);
    });
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