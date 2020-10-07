# -*- coding: utf-8 -*-
# Copyright (c) 2020, Aerele and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import json
from frappe.model.document import Document
import barcode
from frappe import _
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from erpnext.regional.india.utils import get_gst_accounts, get_itemised_tax_breakup_data

class EWBAPIIntegrationSettings(Document):
	pass

def set_field_values(doc, action):
	if action == 'on_submit':
		doc.ewaybill = None
		doc.ewaybill_barcode = None
		doc.save()

def set_ewaybill_barcode(doc, action):
	if action == "before_update_after_submit":
		if doc.ewaybill:
			code = barcode.Code128(str(doc.ewaybill))
			display_code = f'{str(doc.ewaybill)[0:4]} {str(doc.ewaybill)[4:8]} {str(doc.ewaybill)[8:12]}'
			barcode_svg = code.render(writer_options={'module_width': 0.4, 'module_height': 6, 'text_distance': 3, 'font_size':10}, text=display_code).decode()
			doc.ewaybill_barcode = barcode_svg

def make_custom_field():
	custom_fields = {
		'Sales Invoice': [
		{
			"fieldname": "ewaybill_barcode",
			"fieldtype": "Code",
			"label": "E- Way Bill",
			"allow_on_submit": 1,
			"read_only": 1,
			"hidden": 1
			}
		]
	}
	create_custom_fields(custom_fields, ignore_validate=frappe.flags.in_patch, update=True)

# Calculation might be client specific. Will not work if the item specific taxes included.
def calculate_amounts(dt, dn):
	dn = json.loads(dn)
	sinv_doc = frappe.get_doc(dt, dn[0])
	gst_account_heads = get_gst_accounts(sinv_doc.company, True)
	cgstValue = 0
	sgstValue = 0
	igstValue = 0
	for row in sinv_doc.taxes:
		if row.account_head in gst_account_heads:
			if gst_account_heads[row.account_head] == 'cgst_account':
				cgstValue += row.tax_amount
			elif gst_account_heads[row.account_head] == 'sgst_account':
				sgstValue += row.tax_amount
			elif gst_account_heads[row.account_head] == 'igst_account':
				igstValue += row.tax_amount
			else:
				# raising this error because this function might be irrelavant if cess is applied.
				frappe.throw(_(f'Unsupported tax account type: {gst_account_heads[row.account_head]}. Please Contact Admin.'))

	taxable_value = sinv_doc.grand_total - (cgstValue + sgstValue + igstValue)
	taxable_value_from_item_list = sinv_doc.total
	discount_value = taxable_value_from_item_list - taxable_value
	tax_breakup_default = get_itemised_tax_breakup_data(sinv_doc, True)
	itemList = []
	for hsn, hsn_detail in tax_breakup_default[0].items():
		cgstRate = 0
		sgstRate = 0
		igstRate = 0
		for account_head, details in hsn_detail.items():
			if account_head in gst_account_heads:
				if gst_account_heads[account_head] == 'cgst_account':
					cgstRate = details['tax_rate']
				elif gst_account_heads[account_head] == 'sgst_account':
					sgstRate = details['tax_rate']
				elif gst_account_heads[account_head] == 'igst_account':
					igstRate = details['tax_rate']
				else:
					# raising this error because this function might be irrelavant if cess is applied.
					frappe.throw(_('Unsupported tax account type: {gst_account_heads[row.account_head]}. Please Contact Admin.'))
		hsn_total_amount = tax_breakup_default[1][hsn]
		taxableAmount = hsn_total_amount - ((hsn_total_amount / taxable_value_from_item_list) * discount_value)
		item = {
			'hsnCode': hsn,
			'cgstRate': cgstRate,
			'sgstRate': sgstRate,
			'igstRate': igstRate,
			'taxableAmount': taxableAmount
		}
		itemList.append(item)
	
	return {
		'totInvValue': sinv_doc.grand_total,
		'totalValue': taxable_value,
		'cgstValue': cgstValue,
		'sgstValue': sgstValue,
		'igstValue': igstValue,
		'OthValue': 0,
		'itemList': itemList
	}


def get_config_data(gstin):
	api_config_doc = frappe.get_single('EWB API Integration Settings')
	for row in api_config_doc.gstin_credential_mapping:
		if row.gstin == gstin:
			return {'api_key': api_config_doc.api_key, 
				'api_secret': api_config_doc.api_secret, 
				'username': row.username,
				'password': row.password,
				'env': api_config_doc.staging}
