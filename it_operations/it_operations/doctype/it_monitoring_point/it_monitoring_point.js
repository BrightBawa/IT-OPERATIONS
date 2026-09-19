const equipment_type_by_point_type = {
	Camera: "CCTV Camera",
	"Network Video Recorder": "Network Video Recorder",
	Television: "Television",
	"Wireless Access Point": "Wireless Access Point",
	"Network Switch": "Network Switch",
	Router: "Router",
	Server: "Server",
	"Network Endpoint": ["in", ["Computer", "Printer"]],
	Other: "Other",
};

frappe.ui.form.on("IT Monitoring Point", {
	setup(frm) {
		frm.set_query("equipment", () => ({
			filters: {
				is_active: 1,
				...(frm.doc.location ? { location: frm.doc.location } : {}),
				...(equipment_type_by_point_type[frm.doc.point_type]
					? { equipment_type: equipment_type_by_point_type[frm.doc.point_type] }
					: {}),
			},
		}));
	},

	location(frm) {
		if (frm.doc.equipment) {
			frm.set_value("equipment", null);
		}
	},

	point_type(frm) {
		if (frm.doc.equipment) {
			frm.set_value("equipment", null);
		}
	},
});
