frappe.ui.form.on("IT Responsibility Assignment", {
	setup(frm) {
		frm.set_query("responsibility_type", () => ({ filters: { is_active: 1 } }));
		frm.set_query("checklist_template", () => ({
			filters: {
				is_active: 1,
				...(frm.doc.responsibility_type
					? { responsibility_type: frm.doc.responsibility_type }
					: {}),
			},
		}));
	},

	responsibility_type(frm) {
		if (frm.doc.checklist_template) {
			frm.set_value("checklist_template", null);
		}
	},
});
