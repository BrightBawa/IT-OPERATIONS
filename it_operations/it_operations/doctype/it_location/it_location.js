frappe.ui.form.on("IT Location", {
	setup(frm) {
		frm.set_query("parent_location", () => ({
			filters: {
				is_group: 1,
				is_active: 1,
			},
		}));
	},
});
