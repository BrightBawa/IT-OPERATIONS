frappe.listview_settings["IT Daily Operations Log"] = {
	onload(listview) {
		listview.page.add_inner_button(__("Generate / Regenerate Today"), () => {
			frappe.call({
				method: "it_operations.api.operations.regenerate_daily_log",
				freeze: true,
				freeze_message: __("Preparing today's operations log..."),
			}).then(({ message }) => {
				frappe.show_alert({
					message: message && message.length
						? __("Today's operations log is ready.")
						: __("No active responsibility assignments were found."),
					indicator: message && message.length ? "green" : "orange",
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
