# coding=utf-8
__author__ = 'Valentin Grouès'

from flask_assets import Bundle

typeahead_js = Bundle('vendor/node_modules/typeahead.js/dist/typeahead.bundle.js')
handlebars_js = Bundle('vendor/node_modules/handlebars/dist/handlebars.js')
jqueryui_css = Bundle('vendor/node_modules/jquery-ui-dist/jquery-ui.css')
jqueryui_js = Bundle('vendor/node_modules/jquery-ui-dist/jquery-ui.js')

common_css = Bundle(
    'vendor/node_modules/bootstrap/dist/css/bootstrap.css',
    'vendor/node_modules/bootstrap-material-design/dist/css/ripples.css',
    jqueryui_css,
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
    handlebars_js,
    typeahead_js,
    'js/main.js',
    filters='closure_js',
    output='public/js/common.min.js', debug=False)

select2_js = Bundle('vendor/select2/js/select2.full.js', 'vendor/select2/js/select2.sortable.js')

select2_css = Bundle('vendor/select2/css/select2.css', 'vendor/select2/css/select2-bootstrap.css')
