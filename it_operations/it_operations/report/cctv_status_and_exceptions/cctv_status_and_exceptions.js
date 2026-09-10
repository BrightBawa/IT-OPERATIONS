frappe.query_reports["CCTV Status and Exceptions"] = {
	filters: [
		{ fieldname: "from_date", label: __("From Date"), fieldtype: "Date", default: frappe.datetime.add_days(frappe.datetime.get_today(), -7), reqd: 1 },
		{ fieldname: "to_date", label: __("To Date"), fieldtype: "Date", default: frappe.datetime.get_today(), reqd: 1 },
		{ fieldname: "location", label: __("Location"), fieldtype: "Link", options: "IT Location" },
		{ fieldname: "status", label: __("Check Status"), fieldtype: "Select", options: "\nPending\nOK\nFault\nException\nNot Applicable" },
		{ fieldname: "exceptions_only", label: __("Faults / Exceptions Only"), fieldtype: "Check", default: 0 },
	],
};
