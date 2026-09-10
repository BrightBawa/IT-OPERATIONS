frappe.ui.form.on("IT Daily Operations Log", {
	refresh(frm) {
		if (frm.doc.docstatus !== 0) return;

		frm.add_custom_button(__("Regenerate from Assignments"), () => {
			frm.call("regenerate_from_assignments").then(() => frm.reload_doc());
		});

		frm.add_custom_button(__("Mark Camera Checks OK"), () => {
			(frm.doc.check_items || []).forEach((row) => {
				if (row.check_type === "Camera" && row.status === "Pending") {
					frappe.model.set_value(row.doctype, row.name, "status", "OK");
				}
			});
		});

		frm.add_custom_button(__("Add Activity"), () => {
			const row = frm.add_child("activity_entries", {
				activity_type: "Routine Maintenance",
				occurred_at: frappe.datetime.now_datetime(),
			});
			frm.refresh_field("activity_entries");
			frm.fields_dict.activity_entries.grid.grid_rows_by_docname[row.name].toggle_view(true);
		});
	},
});
