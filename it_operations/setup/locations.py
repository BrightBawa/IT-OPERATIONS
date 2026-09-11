import frappe
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


def seed():
	"""Create campus roots and place the existing Block C hierarchy under SOC."""
	if frappe.db.has_column("IT Location", "lft"):
		rebuild_tree("IT Location")

	campuses = {
		code: ensure_location(name, code, "Campus", campus=branch, description=description)
		for name, code, branch, description in CAMPUS_DEFINITIONS
	}
	block_c = ensure_location("Block C", "BLOCK-C", "Block", parent_location=campuses["SOC"])
	for floor_code, room_count in BLOCK_C_CLASSROOM_FLOORS.items():
		ensure_classroom_floor(block_c, floor_code, room_count)
	_normalize_block_c_labels(block_c)
	rebuild_tree("IT Location")
	_refresh_location_metadata()
	return {"campuses": campuses, "block_c": block_c}


def ensure_classroom_floor(block, floor_code, room_count):
	"""Create a floor and its sequential CR01..CRnn room locations."""
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
):
	filters = {"location_code": location_code, "parent_location": parent_location or ("is", "not set")}
	existing = frappe.db.get_value("IT Location", filters, "name")
	if not existing and location_code == "BLOCK-C":
		existing = frappe.db.get_value("IT Location", {"location_code": location_code}, "name")

	if existing:
		doc = frappe.get_doc("IT Location", existing)
		doc.location_name = location_name
		doc.location_type = location_type
		doc.parent_location = parent_location
		if location_type == "Campus":
			doc.campus = campus
		doc.is_active = 1
		if description:
			doc.description = description
		doc.save(ignore_permissions=True)
		return doc.name

	return frappe.get_doc(
		{
			"doctype": "IT Location",
			"location_name": location_name,
			"location_code": location_code,
			"location_type": location_type,
			"parent_location": parent_location,
			"campus": campus,
			"is_active": 1,
			"description": description,
		}
	).insert(ignore_permissions=True).name


def _normalize_block_c_labels(block_c):
	locations = frappe.get_all(
		"IT Location",
		filters={"name": ("like", "Block C - %")},
		fields=["name", "location_code", "location_type"],
	)
	for location in locations:
		if location.location_type in {"Floor", "Room"} and location.location_code:
			frappe.db.set_value(
				"IT Location",
				location.name,
				{
					"location_name": location.location_code,
					"is_group": 1 if location.location_type == "Floor" else 0,
				},
				update_modified=False,
			)

	frappe.db.set_value("IT Location", block_c, "is_group", 1, update_modified=False)


def _refresh_location_metadata():
	roots = frappe.get_all(
		"IT Location",
		filters={"parent_location": ("is", "not set")},
		fields=["name", "location_name", "location_type"],
		order_by="lft asc",
	)
	for root in roots:
		campus = frappe.db.get_value("IT Location", root.name, "campus")
		frappe.db.set_value(
			"IT Location",
			root.name,
			{"campus": campus, "full_location_path": root.location_name},
			update_modified=False,
		)
		_refresh_children(root.name, campus, root.location_name)


def _refresh_children(parent, campus, parent_path):
	children = frappe.get_all(
		"IT Location",
		filters={"parent_location": parent},
		fields=["name", "location_name", "location_type"],
		order_by="lft asc",
	)
	for child in children:
		child_campus = campus
		path = f"{parent_path} / {child.location_name}"
		frappe.db.set_value(
			"IT Location",
			child.name,
			{"campus": child_campus, "full_location_path": path},
			update_modified=False,
		)
		_refresh_children(child.name, child_campus, path)
