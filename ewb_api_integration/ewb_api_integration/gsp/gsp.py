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
from datetime import datetime
from frappe.core.doctype.version.version import get_diff


gsp_file_dict = {'Adaequare': 'adaequare'}
gsp_name = frappe.db.get_single_value('EWB API Integration Settings','gsp')
module_name = '{relative_path}.{module_name}'.format(
			relative_path='ewb_api_integration.ewb_api_integration.gsp', module_name=gsp_file_dict[gsp_name])
gsp = importlib.import_module(module_name)

@frappe.whitelist()
def generate_eway_bill(dt, dn, additional_val):
	ewb = generate_ewb_json(dt, dn)['billLists'][0]
	ewb.update(calculate_amounts(dt, dn))
	ewb_no, ewb_date, validity = gsp.generate_ewb(ewb)
	dn = json.loads(dn)
	sinv_doc = frappe.get_doc(dt, dn[0])
	sinv_doc.ewaybill = ewb_no
	sinv_doc.ewaybill_date = datetime.strptime(ewb_date, '%d/%m/%Y %I:%M:%S %p')
	if validity:
		sinv_doc.ewaybill_validity = datetime.strptime(validity, '%d/%m/%Y %I:%M:%S %p')
	sinv_doc.save()
	frappe.msgprint(_('E-way bill generated successfully'))

@frappe.whitelist()
def cancel_eway_bill_by_user(doctype, docname):
	doc = frappe.get_doc(doctype, docname)
	if gsp.cancel_ewb(doc):
		doc.ewaybill = ''
		doc.ewaybill_barcode = None
		doc.eway_bill_cancelled = 1
		doc.flags.updater_reference = {
			'doctype': doc.doctype,
			'docname': doc.name,
			'label': _('E-Way Bill Cancelled')
		}
		doc.flags.ignore_validate_update_after_submit = True
		doc.flags.ignore_validate = True
		doc.save()
		frappe.msgprint(_('E-way bill cancelled successfully'))


def cancel_eway_bill(doc, action):
	if action == "on_cancel":
		if doc.ewaybill:
			if gsp.cancel_ewb(doc):
				frappe.msgprint(_('E-way bill cancelled successfully'))

def update_transporter(new_doc, action):
	if action == "on_update_after_submit":
		is_gst_transporter_id_changed = False
		old_doc = new_doc.get_doc_before_save()
		diff = get_diff(old_doc, new_doc)
		
		for changed in diff.changed:
			field, old, new = changed
			if field == 'gst_transporter_id' and not old == new:
				is_gst_transporter_id_changed = True
				break

		if new_doc.ewaybill and new_doc.gst_transporter_id and is_gst_transporter_id_changed:
			if gsp.get_ewb(new_doc):
				if gsp.update_transporter(new_doc):
					frappe.msgprint(_('Transporter updated Successfully'))
