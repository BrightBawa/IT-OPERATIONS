frappe.ui.form.on("IT Daily Operations Log", {
	refresh(frm) {
		if (frm.doc.docstatus !== 0) return;

		frm.add_custom_button(__("Regenerate from Assignments"), () => {
			frm.call("regenerate_from_assignments").then(() => frm.reload_doc());
		});

		frm.add_custom_button(__("Mark All Block Equipment OK"), () => {
			frappe.confirm(__("Confirm that you inspected every listed device and all applicable checks passed."), () => {
				(frm.doc.check_items || []).forEach((row) => {
					if (device_requirements[row.device_kind]) {
						mark_device_ok(row);
					}
				});
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

frappe.ui.form.on("IT Daily Check Item", {
	mark_ok(frm, cdt, cdn) {
		mark_device_ok(frappe.get_doc(cdt, cdn));
	},
});

function mark_device_ok(row) {
	const passing_values = {
		online_status: "Online",
		working_status: "Working",
		alignment_status: "Aligned",
		recording_status: "Recording",
		playback_status: "Working",
	};
	const required_fields = new Set(device_requirements[row.device_kind] || []);
	if (!required_fields.size) return;
	const values = Object.fromEntries(
		Object.entries(passing_values).map(([fieldname, passing_value]) => [
			fieldname,
			required_fields.has(fieldname) ? passing_value : "Not Applicable",
		]),
	);
	values.status = "OK";
	Object.entries(values).forEach(([fieldname, value]) => {
		frappe.model.set_value(row.doctype, row.name, fieldname, value);
	});
}

const device_requirements = {
	"CCTV Camera": ["online_status", "working_status", "alignment_status", "recording_status", "playback_status"],
	"Network Video Recorder": ["online_status", "working_status", "recording_status", "playback_status"],
	Television: ["working_status", "alignment_status", "playback_status"],
	"Wireless Access Point": ["online_status", "working_status"],
	"Network Switch": ["online_status", "working_status"],
	Router: ["online_status", "working_status"],
	Server: ["online_status", "working_status"],
	Computer: ["online_status", "working_status"],
	Printer: ["online_status", "working_status"],
	Other: ["working_status"],
};
