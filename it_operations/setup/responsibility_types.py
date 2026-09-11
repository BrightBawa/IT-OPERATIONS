import frappe


BLOCK_INSPECTION = "Block IT Equipment Inspection"
OLD_BLOCK_C_TEMPLATE = "Block C CCTV Daily Inspection"
BLOCK_C_TEMPLATE = "Block C IT Equipment Daily Inspection"

RESPONSIBILITY_TYPES = (
	{
		"name": BLOCK_INSPECTION,
		"frequency": "Daily",
		"equipment": "CCTV cameras and NVRs, televisions and displays, wireless access points",
		"description": "One technician performs the complete daily IT equipment inspection for an assigned block.",
	},
	{
		"name": "CCTV Equipment Inspection",
		"frequency": "Daily",
		"equipment": "CCTV cameras, NVRs, recording storage",
		"description": "Camera availability, alignment, recording, playback, and recorder health.",
	},
	{
		"name": "TV and Display Inspection",
		"frequency": "Daily",
		"equipment": "Televisions, digital displays, display sources",
		"description": "Power, display quality, input/source, playback, mounting, and physical condition.",
	},
	{
		"name": "Wireless Access Point Inspection",
		"frequency": "Daily",
		"equipment": "Wireless access points and their network links",
		"description": "Power, online state, connectivity, mounting, and visible damage.",
	},
	{
		"name": "Network and Server Room Inspection",
		"frequency": "Daily",
		"equipment": "Routers, switches, servers, UPS units, racks, and environmental checks",
		"description": "Daily infrastructure availability and physical-condition inspection.",
	},
	{
		"name": "General IT Equipment Inspection",
		"frequency": "As Needed",
		"equipment": "Computers, printers, peripherals, and other IT equipment",
		"description": "General operational and physical-condition checks for IT-managed equipment.",
	},
)


def seed():
	"""Create selectable responsibility types and convert Block C to the combined responsibility."""
	for definition in RESPONSIBILITY_TYPES:
		if frappe.db.exists("IT Responsibility Type", definition["name"]):
			continue
		frappe.get_doc(
			{
				"doctype": "IT Responsibility Type",
				"responsibility_type_name": definition["name"],
				"inspection_frequency": definition["frequency"],
				"applicable_equipment": definition["equipment"],
				"description": definition["description"],
				"is_active": 1,
			}
		).insert(ignore_permissions=True)

	if frappe.db.exists("IT Checklist Template", OLD_BLOCK_C_TEMPLATE) and not frappe.db.exists(
		"IT Checklist Template", BLOCK_C_TEMPLATE
	):
		frappe.rename_doc("IT Checklist Template", OLD_BLOCK_C_TEMPLATE, BLOCK_C_TEMPLATE, force=True)

	if frappe.db.exists("IT Checklist Template", BLOCK_C_TEMPLATE):
		frappe.db.set_value(
			"IT Checklist Template",
			BLOCK_C_TEMPLATE,
			{
				"responsibility_type": BLOCK_INSPECTION,
				"description": (
					"Daily Block C IT equipment inspection. It currently includes CCTV cameras and NVRs; "
					"add televisions and wireless access points as their inventories become available."
				),
			},
			update_modified=False,
		)
		for assignment in frappe.get_all(
			"IT Responsibility Assignment",
			filters={"checklist_template": BLOCK_C_TEMPLATE},
			pluck="name",
		):
			frappe.db.set_value(
				"IT Responsibility Assignment",
				assignment,
				"responsibility_type",
				BLOCK_INSPECTION,
				update_modified=False,
			)

	return [definition["name"] for definition in RESPONSIBILITY_TYPES]
