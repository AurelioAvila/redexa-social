# Redexa Social

Private creator analytics for Windows.

[![Latest release](https://img.shields.io/github/v/release/AurelioAvila/redexa-social)](https://github.com/AurelioAvila/redexa-social/releases/latest) [![Latest version in WinGet](https://img.shields.io/winget/v/AurelioAvila.SocialDashboard?label=WinGet&color=0078D4)](https://github.com/microsoft/winget-pkgs/tree/master/manifests/a/AurelioAvila/SocialDashboard)

[Download the latest signed release](https://github.com/AurelioAvila/redexa-social/releases/latest) · [Official website](https://redexa.getcertsprint.com) · [Getting started](https://redexa.getcertsprint.com/getting-started)

![Redexa Social](docs/screenshots/overview.png)

This repository hosts Windows downloads, release notes, public documentation and the release verification tools. Application development continues in a private repository. Existing source snapshots remain available in historical branches, tags and forks; future application source is not published here.

Official updates use signed manifests and Windows binaries signed by Aurelio Avila. Download through the official website, this repository or WinGet:

```powershell
winget install --id AurelioAvila.SocialDashboard --exact
```

The WinGet badge reflects accepted manifests. The downloadable catalog and local clients may lag behind a newly merged update. Run `winget source update --name winget`, then `winget show --id AurelioAvila.SocialDashboard --exact --source winget` to check the version available to your client. Use the latest signed GitHub release if the catalog still shows an earlier version.

For private support or billing questions, email [redexasocial@getcertsprint.com](mailto:redexasocial@getcertsprint.com) or use **Help & support** inside the app. For a reproducible, non-sensitive bug, [open an issue](https://github.com/AurelioAvila/redexa-social/issues). Never include passwords, access tokens or private analytics in public issues.

See [privacy](https://redexa.getcertsprint.com/privacy), [plans](https://redexa.getcertsprint.com/pricing) and [license](LICENSE).
