CREATE TABLE `reader_comments` (
	`operation` text PRIMARY KEY NOT NULL,
	`edition` text NOT NULL,
	`item` text NOT NULL,
	`body` text NOT NULL,
	`created_at` integer NOT NULL
);
--> statement-breakpoint
CREATE INDEX `comments_retention` ON `reader_comments` (`created_at`);--> statement-breakpoint
CREATE TABLE `reader_feedback` (
	`operation` text PRIMARY KEY NOT NULL,
	`kind` text NOT NULL,
	`edition` text NOT NULL,
	`item` text NOT NULL,
	`value` text NOT NULL,
	`created_at` integer NOT NULL
);
--> statement-breakpoint
CREATE INDEX `feedback_item_kind` ON `reader_feedback` (`item`,`kind`);--> statement-breakpoint
CREATE TABLE `reader_watchlist_ballots` (
	`topic` text NOT NULL,
	`ballot` text NOT NULL,
	`choice` text NOT NULL,
	`revision` integer NOT NULL,
	`updated_at` integer NOT NULL,
	PRIMARY KEY(`topic`, `ballot`)
);
