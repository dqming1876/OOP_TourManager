CREATE TABLE `accounts` (
 `id` text PRIMARY KEY NOT NULL,
 `username` text NOT NULL,
 `name` text NOT NULL,
 `password_hash` text NOT NULL,
 `salt` text NOT NULL,
 `email` text DEFAULT '' NOT NULL,
 `phone` text DEFAULT '' NOT NULL,
 `address` text DEFAULT '' NOT NULL,
 `birthday` text DEFAULT '' NOT NULL
);
--> statement-breakpoint
CREATE UNIQUE INDEX `accounts_username_unique` ON `accounts` (`username`);
