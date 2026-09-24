import {sqliteTable,text,integer,primaryKey,index} from 'drizzle-orm/sqlite-core';
// Each operation is its own durable fact. A unique operation key makes retries safe.
export const feedback=sqliteTable('reader_feedback',{
 operation:text('operation').primaryKey(), kind:text('kind').notNull(),
 edition:text('edition').notNull(),item:text('item').notNull(),
 value:text('value').notNull(),createdAt:integer('created_at').notNull(),
},t=>[index('feedback_item_kind').on(t.item,t.kind)]);
export const comments=sqliteTable('reader_comments',{
 operation:text('operation').primaryKey(),edition:text('edition').notNull(),
 item:text('item').notNull(),body:text('body').notNull(),createdAt:integer('created_at').notNull(),
},t=>[index('comments_retention').on(t.createdAt)]);
export const watchlist=sqliteTable('reader_watchlist_ballots',{
 topic:text('topic').notNull(),ballot:text('ballot').notNull(),
 choice:text('choice').notNull(),revision:integer('revision').notNull(),
 updatedAt:integer('updated_at').notNull(),
},t=>[primaryKey({columns:[t.topic,t.ballot]})]);
