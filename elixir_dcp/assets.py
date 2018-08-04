# coding=utf-8
__author__ = 'Valentin Grouès'

from flask_assets import Bundle

typeahead_js = Bundle('vendor/node_modules/typeahead.js/dist/typeahead.bundle.js')
handlebars_js = Bundle('vendor/node_modules/handlebars/dist/handlebars.js')
jqueryui_css = Bundle('vendor/node_modules/jquery-ui-dist/jquery-ui.css')
jqueryui_js = Bundle('vendor/node_modules/jquery-ui-dist/jquery-ui.js')
datatables_js = 'vendor/datatables/datatables.min.js'
datatables_css = 'vendor/datatables/datatables.min.css'

select2_js = Bundle('vendor/select2/js/select2.full.js', 'vendor/select2/js/select2.sortable.js')
select2_css = Bundle('vendor/select2/css/select2.css', 'vendor/select2/css/select2-bootstrap.css')


cookiebanner_js =  Bundle('vendor/cookiebanner.min.js')

common_css = Bundle(
    'vendor/node_modules/bootstrap/dist/css/bootstrap.css',
    'vendor/node_modules/bootstrap-material-design/dist/css/ripples.css',
    jqueryui_css,
    datatables_css,
    select2_css,
    Bundle(
        'css/layout.less',
        filters='less'
    ),
    filters='cssmin', output='public/css/common.min.css', debug=False)

common_js = Bundle(
    'vendor/node_modules/jquery/dist/jquery.js',
    'vendor/node_modules/bootstrap/dist/js/bootstrap.js',
    'vendor/node_modules/bootstrap-material-design/dist/js/ripples.js',
    'vendor/node_modules/bootstrap-material-design/dist/js/material.js',
    jqueryui_js,
    select2_js,
    datatables_js,
    handlebars_js,
    typeahead_js,
    'js/main.js',
    filters='closure_js',
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
submission_dish_inline_js = Bundle(
    Bundle(
        'js/submission_dish_inline.js',
        filters='closure_js'
    ),
    output='public/js/submission_dish_inline.min.js')

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

signup_js = Bundle(
    Bundle(
        'js/signup.js',
        filters='closure_js'
    ),
    output='public/js/signup.min.js')

