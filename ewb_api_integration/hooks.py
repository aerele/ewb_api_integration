# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from . import __version__ as app_version

app_name = "ewb_api_integration"
app_title = "Ewb Api Integration"
app_publisher = "Aerele"
app_description = "Implementation of Eway Bill API Integration for India"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "admin@aerele.in"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/ewb_api_integration/css/ewb_api_integration.css"
# app_include_js = "/assets/ewb_api_integration/js/ewb_api_integration.js"

# include js, css files in header of web template
# web_include_css = "/assets/ewb_api_integration/css/ewb_api_integration.css"
# web_include_js = "/assets/ewb_api_integration/js/ewb_api_integration.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "ewb_api_integration/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "ewb_api_integration.install.before_install"
# after_install = "ewb_api_integration.install.after_install"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "ewb_api_integration.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
#	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"ewb_api_integration.tasks.all"
# 	],
# 	"daily": [
# 		"ewb_api_integration.tasks.daily"
# 	],
# 	"hourly": [
# 		"ewb_api_integration.tasks.hourly"
# 	],
# 	"weekly": [
# 		"ewb_api_integration.tasks.weekly"
# 	]
# 	"monthly": [
# 		"ewb_api_integration.tasks.monthly"
# 	]
# }

# Testing
# -------

# before_tests = "ewb_api_integration.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "ewb_api_integration.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "ewb_api_integration.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

doctype_js = {
    "Sales Invoice" : "public/js/sales_invoice.js",
}

doc_events = {
	"Sales Invoice": {
		"before_insert": "ewb_api_integration.ewb_api_integration.doctype.ewb_api_integration_settings.ewb_api_integration_settings.set_field_values",
		"on_update_after_submit": "ewb_api_integration.ewb_api_integration.gsp.gsp.update_transporter",
		"on_cancel": "ewb_api_integration.ewb_api_integration.gsp.gsp.cancel_eway_bill",
		"before_update_after_submit": "ewb_api_integration.ewb_api_integration.doctype.ewb_api_integration_settings.ewb_api_integration_settings.set_ewaybill_barcode"
	}
}

after_install = "ewb_api_integration.ewb_api_integration.doctype.ewb_api_integration_settings.ewb_api_integration_settings.make_custom_field"
