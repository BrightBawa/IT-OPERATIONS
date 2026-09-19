const point_type_by_equipment_type = {
	"CCTV Camera": "Camera",
	"Network Video Recorder": "Network Video Recorder",
	Television: "Television",
	"Wireless Access Point": "Wireless Access Point",
	"Network Switch": "Network Switch",
	Router: "Router",
	Server: "Server",
};

frappe.ui.form.on("IT Equipment", {
	setup(frm) {
		frm.set_query("monitoring_point", () => ({
			filters: {
				is_active: 1,
				...(frm.doc.location ? { location: frm.doc.location } : {}),
				...(point_type_by_equipment_type[frm.doc.equipment_type]
					? { point_type: point_type_by_equipment_type[frm.doc.equipment_type] }
					: {}),
			},
		}));
	},

	location(frm) {
		if (frm.doc.monitoring_point) {
			frm.set_value("monitoring_point", null);
		}
	},

	equipment_type(frm) {
		if (frm.doc.monitoring_point) {
			frm.set_value("monitoring_point", null);
		}
	},
});
