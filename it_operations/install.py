import frappe


ROLES = (
	"IT Operations User",
	"IT Operations Supervisor",
	"IT Operations Manager",
)


def ensure_roles():
	for role_name in ROLES:
		if not frappe.db.exists("Role", role_name):
			frappe.get_doc({"doctype": "Role", "role_name": role_name}).insert(ignore_permissions=True)


def setup_workspace():
	frappe.reload_doc("it_operations", "workspace", "it_operations")
	frappe.clear_cache()


def after_install():
	ensure_roles()
	frappe.db.set_single_value("IT Operations Settings", "enable_daily_generation", 1)
	setup_workspace()
	frappe.db.commit()


def after_migrate():
	ensure_roles()
	if frappe.db.get_single_value("IT Operations Settings", "enable_daily_generation") is None:
		frappe.db.set_single_value("IT Operations Settings", "enable_daily_generation", 1)
	setup_workspace()
	frappe.db.commit()
