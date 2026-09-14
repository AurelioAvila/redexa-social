Redexa Social 1.10.1 makes the application check for a new version every time it opens.

The check asked GitHub at most once a day and answered from its cache otherwise. That cadence suits a background poll, not the moment that matters: opening the application is when somebody is there to be told, and it happens far more rarely than once a day. Anyone who had opened the app in the twenty-four hours before a release was answered from a cache written before that release existed, and would have heard about the update up to a day later.

- The first check after launch always asks GitHub. Every check after it in the same session uses the cache as before, so this is one request per launch rather than one per poll.
- Behaviour when the network is down is unchanged: the last known good answer keeps showing, so an update notice that is already correct does not disappear because the connection dropped.

Windows application, updater and compatibility launcher are signed by Aurelio Avila and timestamped. Code signing identifies the publisher; it does not guarantee acceptance by SmartScreen or antivirus reputation checks.
