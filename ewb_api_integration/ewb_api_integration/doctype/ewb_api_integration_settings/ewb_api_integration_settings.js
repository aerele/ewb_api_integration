// Copyright (c) 2020, Aerele and contributors
// For license information, please see license.txt

frappe.ui.form.on('EWB API Integration Settings', {
	onload: function(frm) {
		frm.set_df_property("gsp","options",['','Adaequare'].join('\n'))
	}
});
