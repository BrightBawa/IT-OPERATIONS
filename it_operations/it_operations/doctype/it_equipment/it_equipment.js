frappe.ui.form.on("IT Equipment", {
	deployment_status(frm) {
		if (frm.doc.deployment_status === "Retired") {
			frm.set_value({ status: "Retired", is_active: 0 });
		}
	},

	status(frm) {
		if (frm.doc.status === "Retired") {
			frm.set_value({ deployment_status: "Retired", is_active: 0 });
		}
	},
});
