# IT Operations

A standalone Frappe app for routine IT checks, CCTV monitoring, operational activities, and daily reporting. It does not depend on or create Helpdesk tickets.

## Initial setup

1. Assign `IT Operations User`, `IT Operations Supervisor`, and `IT Operations Manager` roles as appropriate.
2. Build IT Locations in the tree: Campus → Block/Building → Floor → Room/Outdoor Area. Every non-campus location must belong to a campus hierarchy.
3. Select or create a Responsibility Type, then create Checklist Templates and their mandatory/optional items.
4. Create Responsibility Assignments linking an active Employee, location, responsibility type, supervisor, and template.
5. Leave **Enable Daily Generation** selected in IT Operations Settings.

The daily scheduler creates one draft log for each active assigned employee. Re-running it is idempotent: existing checklist work is retained and only missing assignment/template items are appended. Staff can also use **Generate / Regenerate Today** from the daily-log list or **Regenerate from Assignments** within a draft log.

Access is enforced by server hooks: users see their own logs, supervisors see their own and explicitly assigned team logs, and managers see all records. Submission is blocked until mandatory checks are addressed, and fault/exception rows require remarks. Check, activity, and submission audit fields are stamped on the server.

The **IT Operations** Desk icon opens the standard IT Operations workspace. Its workspace, sidebar, and desktop-icon definitions are shipped with the app and resynchronized after every migration so the Home link cannot point to a missing workspace.

## Location hierarchy

**IT Location** opens in Tree view and starts with the SOC, PAC, and ABC campus roots. Each campus root links to its ERPNext `Branch`: SOC CAMPUS, POMAA ADEISO CAMPUS, or ADEI BROTHERS CAMPUS. Blocks and buildings inherit that Branch from the campus; floors sit below a block or building; rooms and outdoor areas are leaf locations.

Room labels retain their supplied room codes. A separate read-only path identifies the context, for example **SOC Campus / Block C / B08F0 / B08F0CR01**. Human-readable names and codes need only be unique among siblings, so different campuses can each have a Block A or Building 01.

## Block C IT equipment checklist

The initial Block C inventory reuses the general IT Operations model instead of adding a parallel CCTV subsystem:

- `IT Location` stores Block C beneath SOC Campus and preserves the room codes parsed from the supplied channel names.
- Block C includes second floor `B08F2` with classrooms `B08F2CR01` through `B08F2CR08`.
- Room locations have an editable **Assigned Class** link to `Student Batch Name`. The supplied classroom channels populate this field from matching student batches (for example, `10C2-B08F1CR06` links batch `10C2` to room `B08F1CR06`). Corridor channels such as `24CR-0C` and `24CR-1C` are assigned to their corresponding floor and do not receive a class.
- `IT Equipment` stores each of the 23 cameras and 2 NVRs, including camera serial numbers.
- `IT Monitoring Point` stores the device name, model, IP address, channel, and physical location. IP values are operational metadata and can be updated without changing the equipment identity.
- `IT Responsibility Type` provides selectable duties. **Block IT Equipment Inspection** is the umbrella daily responsibility for CCTV/NVRs, televisions/displays, and wireless access points in one assigned block.
- `IT Checklist Template` stores one reusable **Block C IT Equipment Daily Inspection** list. It currently has the 25 supplied CCTV/NVR devices; televisions and access points can be appended when their inventories are supplied.
- `IT Responsibility Assignment` links that template and Block C to the technician chosen by the IT Manager.

## Controlled Block A equipment import

`it_operations.importers.block_a_devices.import_block_a_devices` contains the isolated, idempotent importer for the supplied 55-device SOC Block A inventory. It defaults to a zero-write dry run; pass `dry_run=False` for the controlled import. It creates only the missing Block A location and IT Equipment records, never imports credentials, and skips existing equipment by serial number, MAC address, or IP address and location.
- `IT Daily Operations Log` snapshots the identifying details and records Online, Working, Alignment, Recording, Playback, Overall, and Remarks for each device every day.

The Overall result is calculated on the server. Each equipment type asks only for applicable checks: cameras use online, working, alignment, recording, and playback; NVRs omit alignment; televisions use working, alignment, and playback; access points use online and working. Every applicable check must be completed; any failed value produces a Fault and requires remarks. A per-row **Mark Device OK** action and a confirmation-protected **Mark All Block Equipment OK** action speed up normal inspections without silently recording work. NVR remarks can record storage or hard-drive failures. No CCTV credentials are stored.

The loader creates IT Operations equipment records but does not fabricate ERPNext financial Asset values. Link each equipment record to an ERPNext Asset after its real acquisition date and purchase value are available.

## Installation

```bash
bench get-app <repository-url> --branch version-16
bench --site <site-name> install-app it_operations
```

## License

MIT
