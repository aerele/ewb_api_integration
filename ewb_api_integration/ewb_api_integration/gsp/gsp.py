# -*- coding: utf-8 -*-
# Copyright (c) 2020, Aerele Technologies Private Limited and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
import importlib
import json
from frappe import _
from erpnext.regional.india.utils import generate_ewb_json
from ewb_api_integration.ewb_api_integration.doctype.ewb_api_integration_settings.ewb_api_integration_settings import calculate_amounts



gsp_file_dict = {'Adaequare': 'adaequare'}
gsp_name = frappe.db.get_single_value('EWB API Integration Settings','gsp')
module_name = '{relative_path}.{module_name}'.format(
			relative_path='ewb_api_integration.ewb_api_integration.gsp', module_name=gsp_file_dict[gsp_name])
gsp = importlib.import_module(module_name)

@frappe.whitelist()
def generate_eway_bill(dt, dn, additional_val):
	ewb = generate_ewb_json(dt, dn)
	ewb.update(calculate_amounts(dt, dn))
	ewb_no, ewb_date, validity = gsp.generate_ewb(ewb)
	dn = json.loads(dn)
	sinv_doc = frappe.get_doc(dt, dn[0])
	sinv_doc.ewaybill = ewb_no
	sinv_doc.ewaybill_date = ewb_date
	if validity:
		sinv_doc.ewaybill_validity = validity
	sinv_doc.save()
	frappe.msgprint(_('E-way bill generated successfully'))

def cancel_eway_bill(doc, action):
	if action == "on_cancel":
		if doc.ewaybill:
			if gsp.cancel_ewb(doc):
				frappe.msgprint(_('E-way bill cancelled successfully'))

def update_transporter(doc, action):
	if action == "on_update_after_submit":
		if doc.ewaybill and doc.gst_transporter_id:
			if gsp.get_ewb(doc):
				if gsp.update_transporter(doc):
					frappe.msgprint(_('Transporter updated Successfully'))
