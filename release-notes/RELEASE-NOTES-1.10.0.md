Redexa Social 1.10.0 removes the ceiling that made selling the product its own failure mode, and changes the prices.

The YouTube Data API budget is 10,000 units a day and every copy of this application shares it, because one Google Cloud project is built into the binary. Auto-refresh ran every five minutes for as long as a window was open, minimised or not, and each refresh asked the API for the same channel twice. That is 1,152 units a day from a single idle window, so roughly the tenth simultaneous user broke the product for the nine before them.

- Auto-refresh now runs hourly, and only while the window is actually visible. The Refresh button is unchanged for the moment you want it sooner.
- Each refresh makes one channels.list call instead of two. A channels.list costs one unit however many parts it asks for, so the second call was a unit thrown away every time.
- Together that takes a running copy from 1,152 units a day to at most 72.

Pro is now EUR 7.99 a month and Studio EUR 10.99, with yearly at EUR 49.99 and EUR 69.99. Yearly is about 47% below twelve monthly payments, and the plan cards say 47% rather than the "2 months free" that described the old prices.

The three plans sit on one row with the monthly and yearly switch beside them. The grid used to fall to two columns as soon as the window narrowed, which left Studio alone underneath reading as an afterthought rather than the top tier.

The website can now take a payment. Every pricing button was a link to the download, so the only way to pay was to install the application first and find the upgrade screen inside it. Pro and Studio open a Stripe checkout; VAT is determined and collected there from your billing country. The site also answers a real 404 instead of a JSON method error, and it identifies its seller.

Windows application, updater and compatibility launcher are signed by Aurelio Avila and timestamped. Code signing identifies the publisher; it does not guarantee acceptance by SmartScreen or antivirus reputation checks.
