frappe.ui.form.on("IT Checklist Template", {
	setup(frm) {
		frm.set_query("responsibility_type", () => ({ filters: { is_active: 1 } }));
		frm.set_query("monitoring_point", "items", (doc, cdt, cdn) => {
			const row = frappe.get_doc(cdt, cdn);
			return {
				filters: {
					is_active: 1,
					...(row.check_type === "Camera" ? { point_type: "Camera" } : {}),
				},
			};
		});
		frm.set_query("equipment", "items", () => ({ filters: { is_active: 1 } }));
	},
});
