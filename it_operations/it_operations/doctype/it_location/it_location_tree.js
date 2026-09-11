frappe.treeview_settings["IT Location"] = {
	get_tree_nodes: "it_operations.it_operations.doctype.it_location.it_location.get_children",
	add_tree_node: "it_operations.it_operations.doctype.it_location.it_location.add_node",
	breadcrumb: "IT Operations",
	root_label: "All IT Locations",
	get_tree_root: false,
	ignore_fields: ["parent_location", "campus", "full_location_path"],
	fields: [
		{
			fieldname: "location_name",
			fieldtype: "Data",
			label: __("Location Name / Room Code"),
			reqd: 1,
		},
		{
			fieldname: "location_code",
			fieldtype: "Data",
			label: __("Location Code"),
		},
		{
			fieldname: "location_type",
			fieldtype: "Select",
			label: __("Location Type"),
			options: "Campus\nBlock\nBuilding\nFloor\nRoom\nOutdoor Area\nOther",
			reqd: 1,
		},
		{
			fieldname: "is_group",
			fieldtype: "Check",
			label: __("Can Contain Locations"),
			read_only: 1,
		},
	],
};
