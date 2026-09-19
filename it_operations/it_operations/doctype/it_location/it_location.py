import frappe
from frappe import _
from frappe.utils.nestedset import NestedSet

# ---------------------------------------------------------------------------
# IT LOCATION CONFIGURATION
# ---------------------------------------------------------------------------

GROUP_TYPES = {"Campus", "Block", "Building", "Floor"}
LEAF_TYPES = {"Room", "Outdoor Area", "Other"}

VALID_LOCATION_TYPES = GROUP_TYPES | LEAF_TYPES

ALLOWED_PARENT_TYPES = {
	"Block": {"Campus"},
	"Building": {"Campus"},
	"Floor": {"Block", "Building"},
	"Room": {"Block", "Building", "Floor"},
	"Outdoor Area": {"Campus", "Block", "Building", "Floor"},
	"Other": {"Campus", "Block", "Building", "Floor"},
}


class ITLocation(NestedSet):
	"""
	Hierarchical IT location structure.

	Example:

	    SOC
	    ├── Academic Block
	    │   ├── Floor 1
	    │   │   ├── Room 101
	    │   │   └── Room 102
	    │   └── Floor 2
	    └── Administration Block

	Server-controlled fields:
	    - campus
	    - full_location_path
	    - is_group

	User-controlled structural fields:
	    - location_name
	    - location_code
	    - location_type
	    - parent_location
	    - assigned_class
	    - is_active
	"""

	nsm_parent_field = "parent_location"

	# -----------------------------------------------------------------------
	# NAMING
	# -----------------------------------------------------------------------

	def autoname(self):
		"""
		Generate the document name.

		This retains the existing naming convention so existing code and
		TreeView behaviour do not have to change.

		NOTE:
		For a brand-new system, an immutable ID such as IT-LOC-00001 would
		be preferable. For an existing system, changing the naming scheme
		should be treated as a migration.
		"""

		label = (self.location_name or "").strip()

		if not label:
			frappe.throw(_("Location Name is required."))

		if self.parent_location:
			self.name = f"{self.parent_location} / {label}"
		else:
			self.name = label

	# -----------------------------------------------------------------------
	# VALIDATION
	# -----------------------------------------------------------------------

	def validate(self):
		self._clean_values()
		self._validate_location_type()
		self._validate_location_name()
		self._validate_assigned_class()

		if self.location_type == "Campus":
			self._configure_campus()
		else:
			self._configure_child_location()

		self._set_group_status()

		self._validate_sibling_uniqueness()
		self._validate_location_code_uniqueness()
		self._validate_structure_change()

	def _clean_values(self):
		self.location_name = (self.location_name or "").strip()

		self.location_code = (self.location_code or "").strip().upper() or None

		self.assigned_class = (self.assigned_class or "").strip() or None

	def _validate_location_type(self):
		if not self.location_type:
			frappe.throw(_("Location Type is required."))

		if self.location_type not in VALID_LOCATION_TYPES:
			frappe.throw(_("Invalid Location Type: {0}").format(frappe.bold(self.location_type)))

	def _validate_location_name(self):
		if not self.location_name:
			frappe.throw(_("Location Name is required."))

		if "/" in self.location_name:
			frappe.throw(_("Location Name cannot contain a forward slash (/)."))

		if len(self.location_name) > 140:
			frappe.throw(_("Location Name cannot exceed 140 characters."))

	def _validate_assigned_class(self):
		if self.assigned_class and self.location_type != "Room":
			frappe.throw(_("Assigned Class can only be set for a Room location."))

	# -----------------------------------------------------------------------
	# CAMPUS
	# -----------------------------------------------------------------------

	def _configure_campus(self):
		"""
		Campus is always a root node and must represent exactly one Branch.
		"""

		if self.parent_location:
			frappe.throw(_("A Campus must be a top-level location."))

		if not self.campus:
			frappe.throw(_("Select the Branch represented by this Campus."))

		self.parent_location = None
		self.is_group = 1
		self.full_location_path = self.location_name

		self._validate_unique_campus_branch()

	def _validate_unique_campus_branch(self):
		existing = frappe.db.get_value(
			"IT Location",
			{
				"location_type": "Campus",
				"campus": self.campus,
			},
			"name",
		)

		if existing and existing != self.name:
			frappe.throw(
				_("Branch {0} already has a Campus location: {1}.").format(
					frappe.bold(self.campus),
					frappe.bold(existing),
				)
			)

	# -----------------------------------------------------------------------
	# CHILD LOCATIONS
	# -----------------------------------------------------------------------

	def _configure_child_location(self):
		if not self.parent_location:
			frappe.throw(_("Every non-campus location must have a Parent Location."))

		if self.parent_location == self.name:
			frappe.throw(_("A location cannot be its own parent."))

		parent = frappe.db.get_value(
			"IT Location",
			self.parent_location,
			[
				"name",
				"location_type",
				"location_name",
				"campus",
				"full_location_path",
				"is_group",
				"is_active",
				"lft",
				"rgt",
			],
			as_dict=True,
		)

		if not parent:
			frappe.throw(_("Parent Location {0} does not exist.").format(frappe.bold(self.parent_location)))

		if not parent.is_active:
			frappe.throw(_("Cannot place a location under an inactive Parent Location."))

		if not parent.is_group:
			frappe.throw(_("{0} cannot contain child locations.").format(frappe.bold(parent.location_name)))

		allowed_parents = ALLOWED_PARENT_TYPES.get(
			self.location_type,
			set(),
		)

		if parent.location_type not in allowed_parents:
			frappe.throw(
				_("A {0} cannot be placed under a {1}.").format(
					frappe.bold(self.location_type),
					frappe.bold(parent.location_type),
				)
			)

		self._validate_no_cycle(parent)

		# These values are derived from the parent.
		# Never trust client-supplied values.
		self.campus = parent.campus

		if not self.campus:
			frappe.throw(_("The selected Parent Location is not tied to a Campus."))

		parent_path = parent.full_location_path or parent.location_name

		self.full_location_path = f"{parent_path} / {self.location_name}"

	def _validate_no_cycle(self, parent):
		"""
		Prevent moving a group underneath one of its descendants.

		NestedSet will normally protect the tree as well, but this gives a
		clear application-level validation message.
		"""

		if self.is_new():
			return

		current = frappe.db.get_value(
			"IT Location",
			self.name,
			["lft", "rgt"],
			as_dict=True,
		)

		if not current:
			return

		if not current.lft or not current.rgt:
			return

		if not parent.lft or not parent.rgt:
			return

		if current.lft < parent.lft < current.rgt:
			frappe.throw(
				_("Cannot move {0} below one of its own descendants.").format(frappe.bold(self.location_name))
			)

	# -----------------------------------------------------------------------
	# GROUP / LEAF STATUS
	# -----------------------------------------------------------------------

	def _set_group_status(self):
		if self.location_type in GROUP_TYPES:
			self.is_group = 1

		elif self.location_type in LEAF_TYPES:
			# Prevent a location with children from suddenly becoming a leaf.
			if not self.is_new():
				has_children = frappe.db.exists(
					"IT Location",
					{"parent_location": self.name},
				)

				if has_children:
					frappe.throw(
						_("This location contains child locations and cannot be changed to {0}.").format(
							frappe.bold(self.location_type)
						)
					)

			self.is_group = 0

	# -----------------------------------------------------------------------
	# UNIQUENESS
	# -----------------------------------------------------------------------

	def _validate_sibling_uniqueness(self):
		"""
		Location names must be unique within the same parent.

		Comparison is case-insensitive.
		"""

		parent = self.parent_location or ""

		existing = frappe.db.sql(
			"""
            SELECT name
            FROM `tabIT Location`
            WHERE
                LOWER(TRIM(location_name)) = LOWER(TRIM(%(location_name)s))
                AND IFNULL(parent_location, '') = %(parent)s
                AND name != %(current_name)s
            LIMIT 1
            """,
			{
				"location_name": self.location_name,
				"parent": parent,
				"current_name": self.name or "",
			},
			as_dict=True,
		)

		if existing:
			frappe.throw(
				_("A location named {0} already exists under the selected parent.").format(
					frappe.bold(self.location_name)
				)
			)

	def _validate_location_code_uniqueness(self):
		if not self.location_code:
			return

		parent = self.parent_location or ""

		existing = frappe.db.sql(
			"""
            SELECT name
            FROM `tabIT Location`
            WHERE
                UPPER(TRIM(IFNULL(location_code, '')))
                    = UPPER(TRIM(%(location_code)s))
                AND IFNULL(parent_location, '') = %(parent)s
                AND name != %(current_name)s
            LIMIT 1
            """,
			{
				"location_code": self.location_code,
				"parent": parent,
				"current_name": self.name or "",
			},
			as_dict=True,
		)

		if existing:
			frappe.throw(
				_("Location Code {0} is already used under the selected parent.").format(
					frappe.bold(self.location_code)
				)
			)

	# -----------------------------------------------------------------------
	# STRUCTURAL CHANGES
	# -----------------------------------------------------------------------

	def _validate_structure_change(self):
		"""
		Additional protection for moving existing locations.

		Only users who can write the document should be allowed to alter
		its hierarchy.
		"""

		if self.is_new():
			return

		old_doc = self.get_doc_before_save()

		if not old_doc:
			return

		parent_changed = old_doc.parent_location != self.parent_location

		type_changed = old_doc.location_type != self.location_type

		if parent_changed or type_changed:
			if not frappe.has_permission(
				"IT Location",
				ptype="write",
				doc=self,
				user=frappe.session.user,
			):
				frappe.throw(
					_("You do not have permission to change the location hierarchy."),
					frappe.PermissionError,
				)

	# -----------------------------------------------------------------------
	# UPDATE DESCENDANTS
	# -----------------------------------------------------------------------

	def on_update(self):
		"""
		Let NestedSet perform its own tree maintenance first, then update
		derived metadata for descendants when necessary.
		"""

		super().on_update()

		if self._descendant_refresh_required():
			self._refresh_descendant_metadata()

	def _descendant_refresh_required(self):
		if self.is_new():
			return False

		old_doc = self.get_doc_before_save()

		if not old_doc:
			return False

		return any(
			[
				old_doc.location_name != self.location_name,
				old_doc.parent_location != self.parent_location,
				old_doc.campus != self.campus,
				old_doc.full_location_path != self.full_location_path,
			]
		)

	def _refresh_descendant_metadata(self):
		"""
		Update derived metadata without recursively calling save().

		An iterative queue is used instead of Python recursion to avoid
		recursion-depth problems on malformed or unusually deep trees.
		"""

		queue = [
			{
				"name": self.name,
				"campus": self.campus,
				"path": self.full_location_path,
			}
		]

		visited = set()

		while queue:
			current = queue.pop(0)

			if current["name"] in visited:
				frappe.throw(_("A circular reference was detected in the IT Location hierarchy."))

			visited.add(current["name"])

			children = frappe.get_all(
				"IT Location",
				filters={
					"parent_location": current["name"],
				},
				fields=[
					"name",
					"location_name",
				],
			)

			for child in children:
				child_path = f"{current['path']} / {child.location_name}"

				frappe.db.set_value(
					"IT Location",
					child.name,
					{
						"campus": current["campus"],
						"full_location_path": child_path,
					},
					update_modified=False,
				)

				queue.append(
					{
						"name": child.name,
						"campus": current["campus"],
						"path": child_path,
					}
				)


# ---------------------------------------------------------------------------
# TREE VIEW
# ---------------------------------------------------------------------------


@frappe.whitelist()
def get_children(
	doctype=None,
	parent=None,
	is_root=False,
	**filters,
):
	"""
	Return children for Frappe TreeView.

	frappe.get_list() is deliberately used instead of raw SQL so normal
	Frappe read permissions and permission query conditions are respected.
	"""

	if doctype and doctype != "IT Location":
		frappe.throw(
			_("Invalid DocType."),
			frappe.ValidationError,
		)

	frappe.has_permission(
		"IT Location",
		ptype="read",
		throw=True,
	)

	if parent in (None, "", "All IT Locations"):
		parent_filter = ["is", "not set"]
	else:
		# Ensure the user can read the requested parent.
		if not frappe.has_permission(
			"IT Location",
			ptype="read",
			doc=parent,
			user=frappe.session.user,
		):
			frappe.throw(
				_("You do not have permission to view this location."),
				frappe.PermissionError,
			)

		parent_filter = parent

	locations = frappe.get_list(
		"IT Location",
		filters={
			"parent_location": parent_filter,
			"is_active": 1,
		},
		fields=[
			"name",
			"location_name",
			"is_group",
		],
		order_by="location_name asc",
	)

	return [
		{
			"value": row.name,
			"title": row.location_name,
			"expandable": int(row.is_group or 0),
		}
		for row in locations
	]


# ---------------------------------------------------------------------------
# TREE NODE CREATION
# ---------------------------------------------------------------------------


@frappe.whitelist()
def add_node():
	"""
	Create an IT Location from TreeView.

	Only explicitly permitted fields are accepted from the client.
	Derived/internal fields are calculated by the server.
	"""

	frappe.has_permission(
		"IT Location",
		ptype="create",
		throw=True,
	)

	allowed_fields = {
		"location_name",
		"location_code",
		"location_type",
		"parent_location",
		"assigned_class",
		"is_active",
	}

	data = {}

	for fieldname in allowed_fields:
		value = frappe.form_dict.get(fieldname)

		if value is not None:
			data[fieldname] = value

	parent_location = data.get("parent_location")

	if parent_location == "All IT Locations":
		data["parent_location"] = None

	# Only Campus may be created at root level.
	if not data.get("parent_location"):
		if data.get("location_type") != "Campus":
			frappe.throw(_("Only a Campus can be created at the root level."))

		# Campus is special because Branch must be supplied.
		campus = frappe.form_dict.get("campus")

		if not campus:
			frappe.throw(_("Select the Branch represented by this Campus."))

		data["campus"] = campus

	else:
		# Child campus is always inherited from its parent.
		# Never accept campus supplied by the browser.
		data.pop("campus", None)

	doc = frappe.new_doc("IT Location")

	for fieldname, value in data.items():
		doc.set(fieldname, value)

	doc.insert()

	return {
		"name": doc.name,
		"location_name": doc.location_name,
		"full_location_path": doc.full_location_path,
	}


# ---------------------------------------------------------------------------
# DATABASE INDEXES
# ---------------------------------------------------------------------------


def on_doctype_update():
	"""
	Add indexes required for NestedSet and common hierarchy lookups.

	Application validation remains responsible for the business-specific
	sibling uniqueness rules.
	"""

	frappe.db.add_index(
		"IT Location",
		["lft", "rgt"],
	)

	frappe.db.add_index(
		"IT Location",
		["parent_location"],
	)

	frappe.db.add_index(
		"IT Location",
		["campus"],
	)

	frappe.db.add_index(
		"IT Location",
		["location_type"],
	)

	frappe.db.add_index(
		"IT Location",
		["parent_location", "is_active"],
	)
