frappe.listview_settings["IT Daily Operations Log"] = {
	onload(listview) {
		listview.page.add_inner_button(__("Generate / Regenerate Today"), () => {
			frappe
				.call({
					method: "it_operations.api.operations.regenerate_daily_log",
					freeze: true,
					freeze_message: __("Preparing today's operations log..."),
				})
				.then(({ message }) => {
					const logs = message?.logs || [];
					frappe.show_alert({
						message: message?.message || __("No operations log was generated."),
						indicator: logs.length ? "green" : "orange",
					});
					listview.refresh();
				});
		});
	},
	get_indicator(doc) {
		const indicators = {
			Draft: [__("Draft"), "orange", "status,=,Draft"],
			Submitted: [__("Submitted"), "green", "status,=,Submitted"],
			Cancelled: [__("Cancelled"), "red", "status,=,Cancelled"],
		};
		return indicators[doc.status];
	},
};
