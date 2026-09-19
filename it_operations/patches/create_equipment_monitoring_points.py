import frappe


def execute():
	equipment_records = frappe.get_all(
		"IT Equipment",
		fields=["name", "location"],
		order_by="creation asc",
		limit_page_length=0,
	)
	missing_locations = [row.name for row in equipment_records if not row.location]
	if missing_locations:
		frappe.throw(
			"Every IT Equipment record must have an Asset Location before monitoring points can be created. "
			f"Missing locations: {', '.join(missing_locations)}"
		)

	for row in equipment_records:
		equipment = frappe.get_doc("IT Equipment", row.name)
		equipment._ensure_monitoring_point()
