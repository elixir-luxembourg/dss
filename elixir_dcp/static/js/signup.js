$(document).ready($(function () {
    $('[data-toggle="popover"]').popover();
    $.ajax({
        url: '/autocomplete_institutes'
    }).done(function (data) {
        $('.elx-autocomp-institution').autocomplete({
            source: data,
            minLength: 2
        });
    });
}));