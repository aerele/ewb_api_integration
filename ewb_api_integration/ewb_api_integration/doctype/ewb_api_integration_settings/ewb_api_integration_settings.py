# -*- coding: utf-8 -*-
# Copyright (c) 2020, Aerele and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from erpnext.regional.india.utils import generate_ewb_json

class EWBAPIIntegrationSettings(Document):
	pass

@frappe.whitelist()
def generate_eway_bill(dt, dn, additional_val):
	config_doc = get_ewb_api_config()
	ewb = generate_ewb_json(dt, dn)
	if config_doc.gsp == 'Adaequare':
		from ewb_api_integration.ewb_api_integration.gsp.adaequare import generate_ewb
		generate_ewb(config_doc, ewb, dt, dn)

def get_ewb_api_config():
	''' Returns ewb api config '''
	ewb_api_config = frappe.db.get_singles_dict('EWB API Integration Settings')
	return ewb_api_config