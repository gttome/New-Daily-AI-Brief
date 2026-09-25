CREATE TABLE `cc_migrations` (
	`id` text PRIMARY KEY NOT NULL,
	`payload` text NOT NULL,
	`completed_at` text NOT NULL
);
--> statement-breakpoint
CREATE TABLE `cc_rate_buckets` (
	`bucket` text PRIMARY KEY NOT NULL,
	`count` integer NOT NULL,
	`expires_at` integer NOT NULL
);
--> statement-breakpoint
CREATE TABLE `cc_records` (
	`id` text PRIMARY KEY NOT NULL,
	`family` text NOT NULL,
	`edition` text,
	`payload` text NOT NULL,
	`digest` text NOT NULL,
	`imported_at` text NOT NULL
);
--> statement-breakpoint
CREATE TABLE `cc_revisions` (
	`parent_id` text NOT NULL,
	`revision` integer NOT NULL,
	`request_key` text NOT NULL,
	`request_digest` text NOT NULL,
	`payload` text NOT NULL,
	`created_at` text NOT NULL,
	PRIMARY KEY(`parent_id`, `revision`)
);
--> statement-breakpoint
CREATE UNIQUE INDEX `cc_revisions_request_key_unique` ON `cc_revisions` (`request_key`);--> statement-breakpoint
CREATE TABLE `cc_snapshots` (
	`id` text PRIMARY KEY NOT NULL,
	`edition` text NOT NULL,
	`source_sha` text NOT NULL,
	`payload` text NOT NULL,
	`verified_at` text NOT NULL
);
