frappe.ui.form.on('Sales Invoice', {
	refresh: function(frm) {
		if(frm.doc.docstatus == 1 && !frm.is_dirty()
			&& !frm.doc.is_return && !frm.doc.ewaybill) {
				frm.add_custom_button('Generate E-Way Bill', () => {
					let additional_details = new frappe.ui.Dialog({
						title: 'Are you sure you want to generate?',
						primary_action_label: 'Generate E-Way Bill',
						primary_action(values) {
								additional_details.hide();
								frappe.call({
									method: 'ewb_api_integration.ewb_api_integration.doctype.ewb_api_integration_settings.ewb_api_integration_settings.generate_eway_bill',
									freeze: true,
									args: {
										'dt': frm.doc.doctype,
										'dn': [frm.doc.name],
										'additional_val': values
									},
									callback: function(r) {
										if (r.message) {
											console.log(r.message)
										}
										frm.refresh();
									}
								});
						}
				});
				
				additional_details.show();
	
				}, __("Create"));
			}
}
});