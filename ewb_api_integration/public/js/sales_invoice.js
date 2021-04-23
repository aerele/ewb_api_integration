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
									method: 'ewb_api_integration.ewb_api_integration.gsp.gsp.generate_eway_bill',
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

		if (frm.doc.ewaybill && !frm.doc.eway_bill_cancelled) {
			const action = () => {
				let additional_details = new frappe.ui.Dialog({
					title: 'Are you sure you want to Cancel?',
					primary_action_label: 'Cancel E-Way Bill',
					primary_action() {
							additional_details.hide();
							frappe.call({
								method: 'ewb_api_integration.ewb_api_integration.gsp.gsp.cancel_eway_bill_by_user',
								freeze: true,
								args: {
									'doctype': frm.doc.doctype,
									'docname': frm.doc.name
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
			};
			frm.add_custom_button(__("Cancel E-Way Bill - EWB API"), action, __('E-Way Bill'));
		}
}
});