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
	if action == 'validate' and not doc.docstatus:
		doc.ewaybill = None
		doc.ewaybill_barcode = None
		doc.ewaybill_date = None
		doc.ewaybill_validity = None

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
			dict(fieldname='ewaybill_barcode', label='E- Way Bill',
			fieldtype='Code', allow_on_submit= 1, read_only= 1, hidden= 1 ),
			dict(fieldname='ewaybill_date', label='E- Way Bill Date',
			fieldtype='Data', insert_after='ewaybill', read_only= 1, allow_on_submit= 1, depends_on= 'eval:(doc.docstatus === 1)'),
			dict(fieldname='ewaybill_validity', label='E- Way Bill Validity',
			fieldtype='Data', insert_after='ewaybill_date', read_only= 1, allow_on_submit= 1, depends_on= 'eval:(doc.docstatus === 1)')
		]
	}
	create_custom_fields(custom_fields, update=True)

# Calculation might be client specific. Will not work if the item specific taxes included.
def calculate_amounts(dt, dn):
	hsn_list = []
	total_list = {}
	hsn_taxable_amount_list = {}
	total_taxable_amount_set = {'bool':0}
	total_taxable_amount = {'amount':0.0}
	total_discount = {'amount':0.0}
	cgst_rate = []
	sgst_rate = []
	igst_rate = []
	cgst_amount = []
	sgst_amount = []
	igst_amount = []
	itemList = []
	dn = json.loads(dn)
	sinv_doc = frappe.get_doc(dt, dn[0])
	gst_account_heads = get_gst_accounts(sinv_doc.company, True)
	for row in sinv_doc.items:
		if row.gst_hsn_code not in hsn_list:
			hsn_list.append(row.gst_hsn_code)
	for hsn in hsn_list:
		total_list.update({hsn: 0})
		total_list.update({hsn: total_list[hsn]+1})
		total_list.update({hsn: total_list[hsn]-1})
	for row in sinv_doc.items:
		total_list.update({row.gst_hsn_code: total_list[row.gst_hsn_code] + row.amount})
	for row in sinv_doc.taxes:
		if row.account_head in gst_account_heads:
			if total_taxable_amount_set['bool'] == 0:
				total_taxable_amount_set.update({'bool': 1})
				total_taxable_amount.update({'amount': row.total - row.tax_amount})
			if gst_account_heads[row.account_head] == 'cgst_account':
				cgst_amount.append(row.tax_amount*1.0)
				cgst_rate.append((row.tax_amount/(total_taxable_amount['amount']))*100)
			elif gst_account_heads[row.account_head] == 'sgst_account':
				sgst_amount.append(row.tax_amount*1.0)
				sgst_rate.append((row.tax_amount/(total_taxable_amount['amount']))*100)	
			elif gst_account_heads[row.account_head] == 'igst_account':
				igst_amount.append(row.tax_amount*1.0)
				igst_rate.append((row.tax_amount/(total_taxable_amount['amount']))*100)


	if not cgst_rate:
		cgst_rate.append(0)

	if not sgst_rate:
		sgst_rate.append(0)

	if not igst_rate:
		igst_rate.append(0)

	total_discount.update({'amount':  sinv_doc.total - total_taxable_amount['amount']})

	for hsn in hsn_list:
		temp = total_list[hsn] - ((total_list[hsn]/sinv_doc.total) * total_discount['amount'])
		hsn_taxable_amount_list.update({hsn: temp })

	for hsn in hsn_list:
		item = {
			'hsnCode': hsn,
			'cgstRate': hsn_taxable_amount_list[hsn]*cgst_rate[0]/100,
			'sgstRate': hsn_taxable_amount_list[hsn]*sgst_rate[0]/100,
			'igstRate': hsn_taxable_amount_list[hsn]*igst_rate[0]/100,
			'taxableAmount': hsn_taxable_amount_list[hsn]
		}
		itemList.append(item)

	return {
		'totInvValue': sinv_doc.grand_total,
		'totalValue': total_taxable_amount['amount'],
		'cgstValue': sum(cgst_amount),
		'sgstValue': sum(sgst_amount),
		'igstValue': sum(igst_amount),
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
	frappe.throw(_(f'Kindly update the selected company GSTIN EWB API credentials'))
