import frappe


def execute():
	frappe.db.set_value(
		"IT Equipment",
		{"deployment_status": ("is", "not set")},
		"deployment_status",
		"Deployed",
		update_modified=False,
	)

	for name in frappe.get_all("IT Equipment", pluck="name", order_by="creation asc", limit_page_length=0):
		equipment = frappe.get_doc("IT Equipment", name)
		equipment._ensure_monitoring_point()
