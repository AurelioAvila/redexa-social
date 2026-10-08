# Redexa Social

Private YouTube analytics for Windows. Find your strongest content, spot stalled accounts and plan your next experiment from one local workspace. Your data stays on your PC.

[![Latest release](https://img.shields.io/github/v/release/AurelioAvila/redexa-social)](https://github.com/AurelioAvila/redexa-social/releases/latest) [![Latest version in WinGet](https://img.shields.io/winget/v/AurelioAvila.SocialDashboard?label=WinGet&color=0078D4)](https://github.com/microsoft/winget-pkgs/tree/master/manifests/a/AurelioAvila/SocialDashboard)

[Download the latest signed release](https://github.com/AurelioAvila/redexa-social/releases/latest) · [Official website](https://redexa.getcertsprint.com) · [Getting started](https://redexa.getcertsprint.com/getting-started) · [Plans](https://redexa.getcertsprint.com/pricing)

![Redexa Social overview screen](docs/screenshots/overview.png)

## What it does

- **Single overview.** Start with YouTube analytics. Add Instagram and TikTok with your own developer app and compare trends across connected accounts.
- **Content ranking.** Review your top-performing posts and compare views per post against your own average.
- **Diagnostics, not just numbers.** Flags stalled accounts, zero-view content and access problems, each with a concrete next step. Missing data is not the same as zero performance.
- **Automatic insights.** Computed locally from your own data. No AI calls, no extra cost, nothing sent anywhere.
- **Posting windows and CSV export** (Pro and Studio). A 24-hour chart of posting windows based on the data you collected, and spreadsheet export.
- **12 themes and 6 languages:** English, Spanish, French, German, Italian and Japanese.

Redexa Social reads analytics only. It has no posting, scheduling or automation features and requests no publishing permissions. It complements YouTube Studio; it does not replace every native report.

## Requirements

- Windows 10 or 11, 64-bit.
- A YouTube channel you own or manage. Instagram and TikTok currently require your own developer app. X shows credential status only; X analytics are not available.

## Plans

| | Free | Pro | Studio |
|---|---|---|---|
| Connected accounts | 1 | 3 | 10 |
| Overview, content ranking, diagnostics, local insights | Yes | Yes | Yes |
| Stored history and trend charts | No | Yes | Yes |
| 24-hour posting-window chart | No | Yes | Yes |
| Rivals: compare with up to 3 public channels | No | Yes | Yes |
| CSV export | No | Yes | Yes |
| Computers per licence | No key needed | 3 | 5 |

The free plan is permanent and needs no licence key. Current prices and billing details are on the [pricing page](https://redexa.getcertsprint.com/pricing).

## Install

Download the Windows ZIP from the [latest release](https://github.com/AurelioAvila/redexa-social/releases/latest), extract the whole archive and open `Redexa Social.exe`. Or use WinGet:

```powershell
winget install --id AurelioAvila.SocialDashboard --exact
```

The WinGet badge reflects accepted manifests. The downloadable catalog and local clients may lag behind a newly merged update. Run `winget source update --name winget`, then `winget show --id AurelioAvila.SocialDashboard --exact --source winget` to check the version available to your client. Use the latest signed GitHub release if the catalog still shows an earlier version.

## Verify what you download

Official updates use signed manifests and Windows binaries signed by Aurelio Avila. Before the first run, open the file's **Digital Signatures** tab and check the publisher. Older downloads may be unsigned.

## Privacy

Analytics and saved credentials stay on your PC. The website counts anonymous daily actions without tracking cookies or visitor identifiers. Read the [privacy policy](https://redexa.getcertsprint.com/privacy) for details. You can revoke YouTube access at any time in your Google account settings.

## About this repository

This repository hosts Windows downloads, release notes, public documentation and the release verification tools. Application development continues in a private repository. Existing source snapshots remain available in historical branches, tags and forks; future application source is not published here.

## Support

For private support or billing questions, email [redexasocial@getcertsprint.com](mailto:redexasocial@getcertsprint.com) or use **Help & support** inside the app. For a reproducible, non-sensitive bug, [open an issue](https://github.com/AurelioAvila/redexa-social/issues). Never include passwords, access tokens or private analytics in public issues.

See also the [terms](https://redexa.getcertsprint.com/terms) and the [license](LICENSE).
