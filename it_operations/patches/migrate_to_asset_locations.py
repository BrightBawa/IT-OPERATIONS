import frappe
from frappe.utils.nestedset import rebuild_tree

from it_operations.setup.locations import ensure_asset_location_setup, ensure_location


LOCATION_REFERENCE_DOCTYPES = (
	"IT Equipment",
	"IT Monitoring Point",
	"IT Responsibility Assignment",
	"IT Daily Check Item",
	"IT Activity Entry",
)


def execute():
	migrate_to_asset_locations()


def migrate_to_asset_locations():
	"""Copy the legacy IT Location tree and repoint all IT Operations location links."""
	ensure_asset_location_setup()
	legacy_locations = frappe.get_all(
		"IT Location",
		fields=[
			"name",
			"location_name",
			"location_code",
			"location_type",
			"parent_location",
			"campus",
			"assigned_class",
			"description",
		],
		order_by="lft asc",
		limit_page_length=0,
	)
	mapping = {}
	for legacy in legacy_locations:
		parent = mapping.get(legacy.parent_location) if legacy.parent_location else None
		if legacy.parent_location and not parent:
			frappe.throw(
				f"Cannot migrate IT Location {legacy.name}: parent {legacy.parent_location} was not migrated."
			)
		asset_location = ensure_location(
			legacy.location_name,
			legacy.location_code,
			legacy.location_type,
			parent_location=parent,
			campus=legacy.campus if legacy.location_type == "Campus" else None,
			description=legacy.description,
			assigned_class=legacy.assigned_class,
		)
		if legacy.location_type == "Room" and frappe.get_meta("Location").has_field("custom_room_code"):
			frappe.db.set_value(
				"Location", asset_location, "custom_room_code", legacy.location_code, update_modified=False
			)
		mapping[legacy.name] = asset_location

	rebuild_tree("Location")
	for doctype in LOCATION_REFERENCE_DOCTYPES:
		for old_location, asset_location in mapping.items():
			frappe.db.set_value(
				doctype,
				{"location": old_location},
				"location",
				asset_location,
				update_modified=False,
			)
		_verify_location_links(doctype)

	frappe.clear_cache()
	return {"locations_migrated": len(mapping), "reference_doctypes": LOCATION_REFERENCE_DOCTYPES}


def _verify_location_links(doctype):
	invalid = frappe.db.sql(
		f"""
			select source.name, source.location
			from `tab{doctype}` source
			left join `tabLocation` location on location.name = source.location
			where ifnull(source.location, '') != '' and location.name is null
			limit 1
		""",
		as_dict=True,
	)
	if invalid:
		frappe.throw(
			f"{doctype} {invalid[0].name} still references an invalid Asset Location: "
			f"{invalid[0].location}."
		)
