# IT Operations

A standalone Frappe app for routine IT checks, CCTV monitoring, operational activities, and daily reporting. It does not depend on or create Helpdesk tickets.

## Initial setup

1. Assign `IT Operations User`, `IT Operations Supervisor`, and `IT Operations Manager` roles as appropriate.
2. Create IT Locations and Monitoring Points. Locations are records, so campuses, blocks, buildings, and rooms are never hard-coded.
3. Create Checklist Templates and their mandatory/optional items.
4. Create Responsibility Assignments linking an active Employee, location, responsibility type, supervisor, and template.
5. Leave **Enable Daily Generation** selected in IT Operations Settings.

The daily scheduler creates one draft log for each active assigned employee. Re-running it is idempotent: existing checklist work is retained and only missing assignment/template items are appended. Staff can also use **Generate / Regenerate Today** from the daily-log list or **Regenerate from Assignments** within a draft log.

Access is enforced by server hooks: users see their own logs, supervisors see their own and explicitly assigned team logs, and managers see all records. Submission is blocked until mandatory checks are addressed, and fault/exception rows require remarks. Check, activity, and submission audit fields are stamped on the server.

## Installation

```bash
bench get-app <repository-url> --branch version-16
bench --site <site-name> install-app it_operations
```

## License

MIT
