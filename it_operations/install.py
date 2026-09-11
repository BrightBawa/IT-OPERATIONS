import frappe
from frappe.modules.import_file import import_file_by_path


ROLES = (
	"IT Operations User",
	"IT Operations Supervisor",
	"IT Operations Manager",
)

APP_NAME = "it_operations"
WORKSPACE_NAME = "it_operations"


def ensure_roles():
	for role_name in ROLES:
		if not frappe.db.exists("Role", role_name):
			frappe.get_doc({"doctype": "Role", "role_name": role_name}).insert(ignore_permissions=True)


def setup_workspace():
	frappe.reload_doc("it_operations", "workspace", WORKSPACE_NAME, force=True)
	for folder_name in ("workspace_sidebar", "desktop_icon"):
		import_file_by_path(
			frappe.get_app_path(APP_NAME, folder_name, f"{WORKSPACE_NAME}.json"),
			force=True,
			ignore_version=True,
		)
	frappe.clear_cache()


def after_install():
	from it_operations.setup.block_c_cctv import seed
	from it_operations.setup.locations import seed as seed_locations
	from it_operations.setup.responsibility_types import seed as seed_responsibility_types

	ensure_roles()
	frappe.db.set_single_value("IT Operations Settings", "enable_daily_generation", 1)
	setup_workspace()
	seed_responsibility_types()
	seed_locations()
	seed()
	frappe.db.commit()


def after_migrate():
	from it_operations.setup.locations import ensure_asset_location_setup

	ensure_roles()
	ensure_asset_location_setup()
	if frappe.db.get_single_value("IT Operations Settings", "enable_daily_generation") is None:
		frappe.db.set_single_value("IT Operations Settings", "enable_daily_generation", 1)
	setup_workspace()
	frappe.db.commit()
