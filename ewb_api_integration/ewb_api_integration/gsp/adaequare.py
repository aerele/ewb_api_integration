# -*- coding: utf-8 -*-
# Copyright (c) 2020, Aerele Technologies Private Limited and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
# from erpnext.regional.india.utils import generate_ewb_json
from requests import request
import json
import random, string
from frappe import _
from frappe.utils import cint
from ewb_api_integration.ewb_api_integration.doctype.ewb_api_integration_settings.ewb_api_integration_settings import get_config_data

url_dict = {'base_url': 'https://gsp.adaequare.com',
			'authenticate_url': '/gsp/authenticate?grant_type=token',
			'staging_generate_url': '/test/enriched/ewb/ewayapi?action=GENEWAYBILL',
			'live_generate_url': '/enriched/ewb/ewayapi?action=GENEWAYBILL',
			'staging_cancel_url': '/test/enriched/ewb/ewayapi?action=CANEWB',
			'live_cancel_url': '/enriched/ewb/ewayapi?action=CANEWB',
			'staging_update_transporter_url': '/test/enriched/ewb/ewayapi?action=UPDATETRANSPORTER',
			'live_update_transporter_url': '/enriched/ewb/ewayapi?action=UPDATETRANSPORTER',
			'staging_get_ewb_url': '/test/enriched/ewb/ewayapi/GetEwayBill',
			'live_get_ewb_url': '/enriched/ewb/ewayapi/GetEwayBill'}

def generate_ewb(ewb):
	data = make_supporting_request_data(ewb)
	config_data = get_config_data(data['userGstin'])
	# TODO: put this in a common fn
	url = url_dict['base_url'] + url_dict['live_generate_url']
	if cint(config_data['env']):
		url = url_dict['base_url'] + url_dict['staging_generate_url']

	if 'transporterId' in data and data['transporterId']:
		if 'transDocNo' in data:
			del data['transDocNo']
		if 'transMode' in data:
			del data['transMode']
		if 'vehicleNo' in data:
			del data['vehicleNo']

	payload = json.dumps(data)
	headers = {
	'Content-Type': 'application/json',
	'username': config_data['username'],
	'gstin': data['userGstin'],
	'password': config_data['password'],
	'requestid': ''.join(random.choice(string.ascii_letters) for i in range(5)),
	'Authorization': get_access_token(config_data)
	}
	response = request("POST", url, headers=headers, data=payload)
	response_json = json.loads(response.text.encode('utf8'))
	if response_json['success']:
		return response_json['result']['ewayBillNo'], response_json['result']['ewayBillDate'], response_json['result']['validUpto']
	frappe.throw(response.text, title='ewaybill generation error')

def cancel_ewb(doc):
	# TODO: remove doc dependency from this file
	config_data = get_config_data(doc.company_gstin)
	url = url_dict['base_url'] + url_dict['live_cancel_url']
	if cint(config_data['env']):
		url = url_dict['base_url'] + url_dict['staging_cancel_url']

	payload = json.dumps({
		"ewbNo": doc.ewaybill,
		"cancelRsnCode": 2
	})
	headers = {
	'Content-Type': 'application/json',
	'username': config_data['username'],
	'gstin': doc.company_gstin,
	'password': config_data['password'],
	'requestid': ''.join(random.choice(string.ascii_letters) for i in range(5)),
	'Authorization': get_access_token(config_data)
	}
	response = request("POST", url, headers=headers, data=payload)
	response_json = json.loads(response.text.encode('utf8'))
	if response_json['success']:
		return True
	frappe.throw(response.text, title='ewaybill cancellation error')

def update_transporter(doc):
	# TODO: remove doc dependency from this file
	config_data = get_config_data(doc.company_gstin)
	url = url_dict['base_url'] + url_dict['live_update_transporter_url']
	if cint(config_data['env']):
		url = url_dict['base_url'] + url_dict['staging_update_transporter_url']

	payload = json.dumps({
	"ewbNo": doc.ewaybill,
	"transporterId": doc.gst_transporter_id
	})
	headers = {
	'Content-Type': 'application/json',
	'username': config_data['username'],
	'gstin': doc.company_gstin,
	'password': config_data['password'],
	'requestid': ''.join(random.choice(string.ascii_letters) for i in range(5)),
	'Authorization': get_access_token(config_data)
	}

	response = request("POST", url, headers=headers, data=payload)
	response_json = json.loads(response.text.encode('utf8'))
	if response_json['success']:
		return True
	frappe.throw(response.text, title='Transporter update error')

def get_ewb(doc):
	# TODO: remove doc dependency from this file
	config_data = get_config_data(doc.company_gstin)
	url = url_dict['base_url'] + url_dict['live_get_ewb_url']
	if cint(config_data['env']):
		url = url_dict['base_url'] + url_dict['staging_get_ewb_url']

	headers = {
	'Content-Type': 'application/json',
	'username': config_data['username'],
	'gstin': doc.company_gstin,
	'password': config_data['password'],
	'requestid': ''.join(random.choice(string.ascii_letters) for i in range(5)),
	'Authorization': get_access_token(config_data)
	}

	params ={'ewbNo': doc.ewaybill}
	response = request("GET", url, headers=headers, params= params)
	response_json = json.loads(response.text.encode('utf8'))
	# TODO: either rename this or a seperate function to check transport_id may be not in this file... "get_ewb" function should only get the ewb
	if response_json['success']:
		if response_json['result']['transporterId'] == doc.gst_transporter_id:
			return False
		return True
	else:
		frappe.throw(response.text, title='Get eWaybill error')

def make_supporting_request_data(ewb):
	# TODO: check if this is common for all gsp's 
	# Note: so far all these changes are due to diff in ewb upload json and ewb api json formats
	mapping_keys = {'actualFromStateCode':'actFromStateCode', 'actualToStateCode':'actToStateCode', 'transType':'transactionType', 'OthValue':'otherValue'}
	for key in mapping_keys:
		if key in ewb:
			ewb[mapping_keys[key]] = ewb[key]
			del ewb[key]
	return ewb

def get_access_token(config_data):
	url = url_dict['base_url'] + url_dict['authenticate_url']
	payload  = {}
	headers = {
		'gspappid': config_data['api_key'],
		'gspappsecret': config_data['api_secret']
	}
	response = request("POST", url, headers=headers, data = payload)
	return "Bearer " + json.loads(response.text.encode('utf8'))['access_token']