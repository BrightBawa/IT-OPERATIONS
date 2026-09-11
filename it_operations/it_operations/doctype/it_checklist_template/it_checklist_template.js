frappe.ui.form.on("IT Checklist Template", {
	setup(frm) {
		frm.set_query("responsibility_type", () => ({ filters: { is_active: 1 } }));
	},
});
