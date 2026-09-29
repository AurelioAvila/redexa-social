# Redexa Social 1.9.3

This release completes the Windows shortcut migration and introduces timestamped Certum signatures for the application, updater and compatibility launcher.

- Existing Social Dashboard desktop shortcuts are renamed to Redexa Social and point to the current executable and icon.
- The application icon is included in the installed resources as well as the executable.
- Repository and release links now use AurelioAvila/redexa-social. Registered legacy Instagram and TikTok callback addresses remain available.
- The update archive and manifest are regenerated after signing, preserving automatic-update verification.

The legacy executable remains as a compatibility launcher for older installations. A valid digital signature identifies the publisher; it does not guarantee acceptance by SmartScreen or antivirus reputation checks.
