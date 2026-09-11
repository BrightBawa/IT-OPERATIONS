import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.permissions import setup_custom_perms
from frappe.utils.nestedset import rebuild_tree


SOC_CAMPUS = "SOC Campus"
PAC_CAMPUS = "PAC Campus"
ABC_CAMPUS = "ABC Campus"

CAMPUS_DEFINITIONS = (
	(SOC_CAMPUS, "SOC", "SOC CAMPUS", "Sam Okudzeto Campus at Sota."),
	(PAC_CAMPUS, "PAC", "POMAA ADEISO CAMPUS", "Pomaa-Adeiso Campus."),
	(ABC_CAMPUS, "ABC", "ADEI BROTHERS CAMPUS", "Adei Brothers Campus."),
)

BLOCK_C_CLASSROOM_FLOORS = {
	"B08F2": 8,
}

LOCATION_TYPES = "Campus\nBlock\nBuilding\nFloor\nRoom\nOutdoor Area\nOther"
GROUP_TYPES = {"Campus", "Block", "Building", "Floor"}
LOCATION_CUSTOM_FIELDS = {
	"Location": (
		{
			"fieldname": "custom_it_operations_details",
			"fieldtype": "Section Break",
			"insert_after": "is_group",
			"label": "IT Operations Details",
		},
		{
			"fieldname": "custom_it_location_type",
			"fieldtype": "Select",
			"insert_after": "custom_it_operations_details",
			"label": "IT Location Type",
			"options": LOCATION_TYPES,
			"in_standard_filter": 1,
		},
		{
			"fieldname": "custom_it_location_code",
			"fieldtype": "Data",
			"insert_after": "custom_it_location_type",
			"label": "IT Location Code",
			"in_list_view": 1,
		},
		{
			"fieldname": "custom_it_location_column",
			"fieldtype": "Column Break",
			"insert_after": "custom_it_location_code",
		},
		{
			"fieldname": "custom_campus_branch",
			"fieldtype": "Link",
			"insert_after": "custom_it_location_column",
			"label": "Campus / Branch",
			"options": "Branch",
			"in_standard_filter": 1,
		},
		{
			"fieldname": "custom_assigned_class",
			"fieldtype": "Link",
			"insert_after": "custom_campus_branch",
			"label": "Assigned Class",
			"options": "Student Batch Name",
			"depends_on": "eval:doc.custom_it_location_type=='Room'",
			"in_standard_filter": 1,
		},
		{
			"fieldname": "custom_it_description",
			"fieldtype": "Small Text",
			"insert_after": "custom_assigned_class",
			"label": "IT Location Description",
		},
	)
}

LOCATION_ROLE_PERMISSIONS = {
	"IT Operations User": {"read": 1},
	"IT Operations Supervisor": {
		"read": 1,
		"write": 1,
		"create": 1,
		"delete": 1,
		"report": 1,
		"export": 1,
		"print": 1,
		"email": 1,
		"share": 1,
	},
	"IT Operations Manager": {
		"read": 1,
		"write": 1,
		"create": 1,
		"delete": 1,
		"report": 1,
		"export": 1,
		"print": 1,
		"email": 1,
		"share": 1,
	},
}


def ensure_asset_location_setup():
	create_custom_fields(LOCATION_CUSTOM_FIELDS, update=True)
	ensure_location_permissions()


def ensure_location_permissions():
	setup_custom_perms("Location")
	for role, permissions in LOCATION_ROLE_PERMISSIONS.items():
		name = frappe.db.get_value(
			"Custom DocPerm", {"parent": "Location", "role": role, "permlevel": 0}, "name"
		)
		if name:
			doc = frappe.get_doc("Custom DocPerm", name)
		else:
			doc = frappe.get_doc(
				{
					"doctype": "Custom DocPerm",
					"parent": "Location",
					"parenttype": "DocType",
					"parentfield": "permissions",
					"role": role,
					"permlevel": 0,
				}
			)
		doc.update(permissions)
		doc.save(ignore_permissions=True)
	frappe.clear_cache(doctype="Location")


def seed():
	"""Create the campus and Block C hierarchy in ERPNext Asset Locations."""
	ensure_asset_location_setup()
	rebuild_tree("Location")
	campuses = {
		code: ensure_location(name, code, "Campus", campus=branch, description=description)
		for name, code, branch, description in CAMPUS_DEFINITIONS
	}
	block_c = ensure_location("Block C", "BLOCK-C", "Block", parent_location=campuses["SOC"])
	for floor_code, room_count in BLOCK_C_CLASSROOM_FLOORS.items():
		ensure_classroom_floor(block_c, floor_code, room_count)
	rebuild_tree("Location")
	return {"campuses": campuses, "block_c": block_c}


def ensure_classroom_floor(block, floor_code, room_count):
	"""Create an Asset Location floor and its sequential CR01..CRnn room locations."""
	floor = ensure_location(floor_code, floor_code, "Floor", parent_location=block)
	rooms = [
		ensure_location(
			f"{floor_code}CR{room_number:02d}",
			f"{floor_code}CR{room_number:02d}",
			"Room",
			parent_location=floor,
		)
		for room_number in range(1, room_count + 1)
	]
	return floor, rooms


def ensure_location(
	location_name,
	location_code,
	location_type,
	parent_location=None,
	campus=None,
	description=None,
	assigned_class=None,
):
	"""Create or reconcile one standard ERPNext Asset Location."""
	existing = frappe.db.get_value("Location", {"location_name": location_name}, "name")
	if existing:
		doc = frappe.get_doc("Location", existing)
		if (doc.parent_location or None) != (parent_location or None):
			frappe.throw(
				f"Asset Location {location_name} already exists beneath {doc.parent_location or 'the root'}, "
				f"not {parent_location or 'the root'}."
			)
	else:
		doc = frappe.new_doc("Location")
		doc.location_name = location_name
		doc.parent_location = parent_location

	branch = campus
	if location_type != "Campus" and parent_location:
		branch = frappe.db.get_value("Location", parent_location, "custom_campus_branch")
	doc.is_group = 1 if location_type in GROUP_TYPES else 0
	doc.custom_it_location_type = location_type
	doc.custom_it_location_code = location_code
	doc.custom_campus_branch = branch
	if assigned_class is not None:
		doc.custom_assigned_class = assigned_class
	if description is not None:
		doc.custom_it_description = description
	doc.save(ignore_permissions=True)
	return doc.name
