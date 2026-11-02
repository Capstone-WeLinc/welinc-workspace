# Project background

> Source: Google Docs "Project Background", "System Description", "Gap Analysis" (Capstone 1, AY 2025–2026). Distilled 2026-10-22. Stable facts only; features and scope live in Jira.

## Client

**WeLinc Logistics** (Philippines), a logistics and transportation company that runs trucks out of three garages: Sta. Rosa (Laguna), Marikina (Metro Manila) and Pulilan (Bulacan). All garages share one system and one database.

## The problem

Repair work is tracked by hand:

- Mechanics log repairs on paper with no shared format. An Excel template and a Google Form were both tried and abandoned, because staff found them hard to use.
- Nobody can see live repair status. Management checks on site.
- Driver details are not recorded, so nobody is accountable for damage.
- Repair costs per truck are not tracked, so profitability can't be judged.
- Finding a truck's repair history means searching paper and scattered files.
- There are no alerts or reports. Everything depends on manual follow up.
- Mechanic assignments are verbal, with no record of who did what.

Current tools: Wix (internal site), Excel, Meta Business Suite (customer bookings), Microsoft Teams (coordination). None of them manage repairs.

## Constraints that shape the design

- **Low digital literacy.** Earlier tools failed for this reason. The UI must be simple and guided, with as few steps as possible.
- **Mechanics use phones.** Garages only have phones; IT has phones and laptops. Mechanic screens must work well on a phone and on a weak connection.
- **Network dependence.** Performance depends on each garage's internet connection.

## Goal

One central place to log, track and cost repairs, with role based access, a repair history per truck, and dashboards and alerts for management.
