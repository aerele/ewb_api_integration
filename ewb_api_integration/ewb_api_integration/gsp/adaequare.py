# -*- coding: utf-8 -*-
# Copyright (c) 2020, Aerele Technologies Private Limited and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from erpnext.regional.india.utils import generate_ewb_json
from requests import request
import json
import random, string
from erpnext.regional.india.utils import get_gst_accounts, get_itemised_tax_breakup_data
from frappe import _
from frappe.utils import cint
from ewb_api_integration.ewb_api_integration.doctype.ewb_api_integration_settings.ewb_api_integration_settings import get_ewb_api_config

base_url = 'https://gsp.adaequare.com'

def generate_ewb(config_doc, ewb, dt, dn):
	data = make_supporting_request_data(ewb['billLists'][0])
	data.update(calculate_amounts(dt, dn))
	generate_url = '/test/enriched/ewb/ewayapi?action=GENEWAYBILL'
	if cint(config_doc.staging):
		url = base_url + generate_url
	else:
		url = base_url + generate_url.replace('/test','')
	
	if 'transporterId' in data:
		if 'transDocNo' in data:
			del data['transDocNo']
		if 'transMode' in data:
			del data['transMode']
		if 'vehicleNo' in data:
			del data['vehicleNo']

	token = get_token(config_doc)
	payload = json.dumps(data)
	headers = {
	'Content-Type': 'application/json',
	'username': config_doc.username,
	'gstin': data['userGstin'],
	'password': config_doc.password,
	'requestid': ''.join(random.choice(string.ascii_letters) for i in range(5)),
	'Authorization': token
	}

	response = request("POST", url, headers=headers, data=payload)
	response_json = json.loads(response.text.encode('utf8'))
	if response_json['success']:
		dn = json.loads(dn)
		sinv_doc = frappe.get_doc(dt, dn[0])
		sinv_doc.ewaybill = response_json['result']['ewayBillNo']
		sinv_doc.save()
		frappe.msgprint(_(response_json['message']))
	else:
		frappe.throw(response.text, title='ewaybill generation error')

def cancel_ewb(doc, action):
	if action == "on_cancel":
		if doc.ewaybill:
			config_doc = get_ewb_api_config()
			generate_url = '/test/enriched/ewb/ewayapi?action=CANEWB'
			if cint(config_doc.staging):
				url = base_url + generate_url
			else:
				url = base_url + generate_url.replace('/test','')

			token = get_token(config_doc)
			payload = json.dumps({
				"ewbNo": doc.ewaybill,
				"cancelRsnCode": 2
			})
			headers = {
			'Content-Type': 'application/json',
			'username': config_doc.username,
			'gstin': doc.company_gstin,
			'password': config_doc.password,
			'requestid': ''.join(random.choice(string.ascii_letters) for i in range(5)),
			'Authorization': token
			}

			response = request("POST", url, headers=headers, data=payload)
			response_json = json.loads(response.text.encode('utf8'))
			if response_json['success']:
				frappe.msgprint(_(response_json['message']))
			else:
				frappe.throw(response.text, title='ewaybill cancellation error')

def make_supporting_request_data(ewb):
	mapping_keys = {'actualFromStateCode':'actFromStateCode', 'actualToStateCode':'actToStateCode', 'transType':'transactionType'}
	for key in mapping_keys:
		if key in ewb:
			ewb[mapping_keys[key]] = ewb[key]
			del ewb[key]
	return ewb

def get_token(config_doc):
	url = base_url + '/gsp/authenticate?grant_type=token'
	client_id = config_doc.api_key
	client_secret = config_doc.api_secret
	payload  = {}
	headers = {
		'gspappid': client_id,
		'gspappsecret': client_secret
	}
	response = request("POST", url, headers=headers, data = payload)
	return "Bearer " + json.loads(response.text.encode('utf8'))['access_token']

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