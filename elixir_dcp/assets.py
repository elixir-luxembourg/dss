# coding=utf-8
__author__ = 'Valentin Grouès'

from flask_assets import Bundle

typeahead_js = Bundle('vendor/node_modules/typeahead.js/dist/typeahead.bundle.js')
handlebars_js = Bundle('vendor/node_modules/handlebars/dist/handlebars.js')
jqueryui_css = Bundle('vendor/node_modules/jquery-ui-dist/jquery-ui.css')
jqueryui_js = Bundle('vendor/node_modules/jquery-ui-dist/jquery-ui.js')
tm_editor_js = Bundle('vendor/node_modules/tinymce/tinymce.min.js')

datatables_css = 'vendor/node_modules/datatables.net-bs5/css/dataTables.bootstrap5.min.css'
datatables_js = Bundle('vendor/node_modules/datatables.net/js/dataTables.min.js',
                       'vendor/node_modules/datatables.net-bs5/js/dataTables.bootstrap5.min.js')

select2_js = Bundle('vendor/node_modules/select2/dist/js/select2.full.js', 
                    'vendor/select2/js/select2.sortable.js')
select2_css = Bundle('vendor/node_modules/select2/dist/css/select2.min.css',
                     'public/css/select2-custom.css')


common_css = Bundle(
    'public/css/bootstrap-custom.css',
    'vendor/node_modules/bootstrap-icons/font/bootstrap-icons.css',
    jqueryui_css,
    datatables_css,
    select2_css,
    filters='cssmin', output='public/css/common.min.css', debug=False)

common_js = Bundle(
    'vendor/node_modules/jquery/dist/jquery.js',
    'vendor/node_modules/bootstrap/dist/js/bootstrap.bundle.min.js',
    jqueryui_js,
    select2_js,
    datatables_js,
    handlebars_js,
    typeahead_js,
    'js/main.js',
    output='public/js/common.min.js', debug=False)

submission_editor_js = Bundle(
    Bundle(
        'js/submission_editor.js',
        filters='closure_js'
    ),
    output='public/js/submission_editor.min.js')

submission_listing_js = Bundle(
    Bundle(
        'js/submission_listing.js',
        filters='closure_js'
    ),
    output='public/js/submission_listing.min.js')
user_editor_js = Bundle(
    Bundle(
        'js/user_editor.js',
        filters='closure_js'
    ),
    output='public/js/user_editor.min.js')

user_listing_js = Bundle(
    Bundle(
        'js/user_listing.js',
        filters='closure_js'
    ),
    output='public/js/user_listing.min.js')


notification_listing_js = Bundle(
    Bundle(
        'js/notification_listing.js',
        filters='closure_js'
    ),
    output='public/js/notification_listing.min.js')
