import frappe
from frappe import _
from frappe.utils.nestedset import NestedSet


GROUP_TYPES = {"Campus", "Block", "Building", "Floor"}
LEAF_TYPES = {"Room", "Outdoor Area", "Other"}
ALLOWED_PARENT_TYPES = {
	"Block": {"Campus"},
	"Building": {"Campus"},
	"Floor": {"Block", "Building"},
	"Room": {"Block", "Building", "Floor"},
	"Outdoor Area": {"Campus", "Block", "Building", "Floor"},
	"Other": {"Campus", "Block", "Building", "Floor"},
}


class ITLocation(NestedSet):
	nsm_parent_field = "parent_location"

	def autoname(self):
		label = (self.location_name or "").strip()
		self.name = f"{self.parent_location} / {label}" if self.parent_location else label

	def validate(self):
		self.location_name = (self.location_name or "").strip()
		self.location_code = (self.location_code or "").strip() or None
		if "/" in self.location_name:
			frappe.throw(_("Location Name cannot contain a forward slash (/)."))

		if self.location_type == "Campus":
			if self.parent_location:
				frappe.throw(_("A Campus must be a top-level location."))
			if not self.campus:
				frappe.throw(_("Select the Branch represented by this Campus."))
			self.is_group = 1
			self.full_location_path = self.location_name
			self._validate_unique_campus_branch()
		else:
			self._set_parent_details()

		if self.location_type in GROUP_TYPES:
			self.is_group = 1
		elif self.location_type in LEAF_TYPES:
			self.is_group = 0

		self._validate_sibling_uniqueness()

	def on_update(self):
		super().on_update()
		self._refresh_descendant_metadata()

	def _set_parent_details(self):
		if not self.parent_location:
			frappe.throw(_("Every non-campus location must have a Parent Location."))
		parent = frappe.db.get_value(
			"IT Location",
			self.parent_location,
			["location_type", "location_name", "campus", "full_location_path", "is_group"],
			as_dict=True,
		)
		if not parent:
			frappe.throw(_("Parent Location {0} does not exist.").format(self.parent_location))
		if not parent.is_group:
			frappe.throw(_("{0} cannot contain child locations.").format(parent.location_name))
		allowed = ALLOWED_PARENT_TYPES.get(self.location_type, set())
		if parent.location_type not in allowed:
			frappe.throw(
				_("A {0} cannot be placed under a {1}.").format(self.location_type, parent.location_type)
			)
		self.campus = parent.campus
		if not self.campus:
			frappe.throw(_("The selected parent is not tied to a Campus."))
		parent_path = parent.full_location_path or parent.location_name
		self.full_location_path = f"{parent_path} / {self.location_name}"

	def _validate_sibling_uniqueness(self):
		filters = {"location_name": self.location_name}
		filters["parent_location"] = self.parent_location or ("is", "not set")
		existing = frappe.db.get_value("IT Location", filters, "name")
		if existing and existing != self.name:
			frappe.throw(_("Location names must be unique within the same parent."))

		if self.location_code:
			code_filters = {"location_code": self.location_code}
			code_filters["parent_location"] = self.parent_location or ("is", "not set")
			existing = frappe.db.get_value("IT Location", code_filters, "name")
			if existing and existing != self.name:
				frappe.throw(_("Location codes must be unique within the same parent."))

	def _validate_unique_campus_branch(self):
		existing = frappe.db.get_value(
			"IT Location",
			{"location_type": "Campus", "campus": self.campus},
			"name",
		)
		if existing and existing != self.name:
			frappe.throw(_("Branch {0} already has a Campus location.").format(self.campus))

	def _refresh_descendant_metadata(self):
		campus = self.campus
		for child in frappe.get_all("IT Location", filters={"parent_location": self.name}, pluck="name"):
			child_doc = frappe.get_doc("IT Location", child)
			path = f"{self.full_location_path} / {child_doc.location_name}"
			frappe.db.set_value(
				"IT Location",
				child,
				{"campus": campus, "full_location_path": path},
				update_modified=False,
			)
			child_doc.campus = campus
			child_doc.full_location_path = path
			child_doc._refresh_descendant_metadata()


@frappe.whitelist()
def get_children(doctype, parent=None, is_root=False, **filters):
	frappe.has_permission("IT Location", "read", throw=True)
	if parent in (None, "", "All IT Locations"):
		parent = ""
	return frappe.db.sql(
		"""
		select name as value, location_name as title, is_group as expandable
		from `tabIT Location`
		where ifnull(parent_location, '') = %(parent)s and is_active = 1
		order by location_name
		""",
		{"parent": parent},
		as_dict=True,
	)


@frappe.whitelist()
def add_node():
	from frappe.desk.treeview import make_tree_args

	args = make_tree_args(**frappe.form_dict)
	if args.parent_location == "All IT Locations":
		args.parent_location = None
	frappe.get_doc(args).insert()


def on_doctype_update():
	frappe.db.add_index("IT Location", ["lft", "rgt"])
