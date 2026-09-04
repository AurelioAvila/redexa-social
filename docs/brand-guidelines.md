# Redexa Social brand guide

## Brand idea

Redexa Social turns fragmented platform statistics into a clear next move for independent creators and small teams.

**Positioning:** The private social analytics workspace for creators who want useful direction without handing their audience data to another cloud dashboard.

**Primary promise:** Turn scattered metrics into your next move.

**Supporting promise:** Your accounts, your data, your decisions.

## Voice

- Clear before clever: explain the outcome in plain English.
- Decisive, not inflated: recommend actions only when the product can support them with data.
- Calm and respectful: never use fear, hype or artificial urgency.
- Specific: prefer “four connected accounts” to “everything in one place.”
- Human: concise sentences, natural contractions and no generic AI language.

## Visual system

| Role | Color | Use |
|---|---|---|
| Ink | `#0B1430` | Headlines and primary text |
| Cobalt | `#145CFF` | Primary actions, selection and brand emphasis |
| Canvas | `#F7F9FC` | Application and website background |
| Surface | `#FFFFFF` | Navigation and grouped content |
| Slate | `#63708A` | Supporting copy |
| Signal green | `#2DBB56` | Positive change only |
| Warning amber | `#D97706` | Attention states only |
| Critical red | `#DC2626` | Errors and destructive actions only |

Use Segoe UI Variable in the Windows application and Inter on the website. Keep layouts spacious, borders quiet and shadows rare. Platform colors identify platforms; they are not decorative brand colors.

## Naming

- Product: **Redexa Social**
- Short reference after first mention: **the app** or **Redexa Social**
- Repository slug remains `social-dashboard` to preserve registered OAuth callbacks, existing links and update infrastructure.
- New installations use the `Redexa Social` executable, app identity and `%APPDATA%\\RedexaSocial` data directory.
- Existing `%APPDATA%\\SocialDashboard` data is migrated automatically, while a lightweight legacy launcher preserves old shortcuts and updater continuity.
- The public website is `https://redexa.getcertsprint.com`; the former hostname is retained only as a compatibility redirect and API bridge for older clients.

## Proof hierarchy

1. Local-first data storage
2. Read-only platform access
3. Cross-platform performance overview
4. Actionable diagnostics and posting-window analysis
5. Exportable data and multilingual interface

Never claim that every platform is immediately available when its public API or app review still limits access.
