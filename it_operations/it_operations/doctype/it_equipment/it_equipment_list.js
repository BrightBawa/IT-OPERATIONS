frappe.listview_settings["IT Equipment"] = {
	get_indicator(doc) {
		if (doc.deployment_status === "Retired") {
			return [__("Retired"), "gray", "deployment_status,=,Retired"];
		}
		if (doc.deployment_status === "In Storage") {
			return [__("In Storage"), "blue", "deployment_status,=,In Storage"];
		}
		if (doc.deployment_status === "Reserved") {
			return [__("Reserved"), "purple", "deployment_status,=,Reserved"];
		}
		if (doc.deployment_status === "Under Maintenance") {
			return [__("Under Maintenance"), "orange", "deployment_status,=,Under Maintenance"];
		}
		if (doc.status === "Operational") {
			return [__("Deployed · Operational"), "green", "deployment_status,=,Deployed"];
		}
		if (doc.status === "Degraded") {
			return [__("Deployed · Degraded"), "orange", "status,=,Degraded"];
		}
		return [__("Deployed · {0}", [doc.status]), "red", `status,=,${doc.status}`];
	},
};
