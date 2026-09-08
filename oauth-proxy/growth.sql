CREATE TABLE IF NOT EXISTS growth_daily (
 day TEXT NOT NULL, product TEXT NOT NULL, event TEXT NOT NULL,
 count INTEGER NOT NULL DEFAULT 0,
 PRIMARY KEY (day, product, event)
);
