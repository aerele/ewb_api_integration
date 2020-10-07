# -*- coding: utf-8 -*-
# Copyright (c) 2020, Aerele Technologies Private Limited and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
import importlib
from erpnext.regional.india.utils import generate_ewb_json



gsp_file_dict = {'Adaequare': 'adaequare'}
gsp_name = frappe.db.get_single_value('EWB API Integration Settings','gsp')
module_name = '{relative_path}.{module_name}'.format(
			relative_path='ewb_api_integration.ewb_api_integration.gsp', module_name=gsp_file_dict[gsp_name])
gsp = importlib.import_module(module_name)

@frappe.whitelist()
def generate_eway_bill(dt, dn, additional_val):
	ewb = generate_ewb_json(dt, dn)
	gsp.generate_ewb(ewb, dt, dn)

def cancel_eway_bill(doc, action):
	if action == "on_cancel":
		if doc.ewaybill:
			gsp.cancel_ewb(doc)

def update_transporter(doc, action):
	if action == "on_update_after_submit":
		if doc.ewaybill and doc.gst_transporter_id:
			if gsp.get_ewb(doc):
				gsp.update_transporter(doc)
