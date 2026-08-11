/**
 * Applies every migrations/*.sql file in filename order, once each.
 *
 *   npm run db:migrate
 *
 * Applied files are recorded in schema_migrations, so re-running is safe.
 * Each file runs inside its own transaction — a failure rolls that file back
 * and stops, leaving earlier migrations applied.
 */
import { readdirSync, readFileSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { Client } from 'pg';

const MIGRATIONS_DIR = join(dirname(fileURLToPath(import.meta.url)), '..', 'migrations');

async function main() {
  const url = process.env.DATABASE_URL;
  if (!url) {
    console.error('DATABASE_URL is not set. Copy .env.example to .env.local and fill it in.');
    process.exit(1);
  }

  const client = new Client({
    connectionString: url,
    ssl: url.includes('localhost') || url.includes('127.0.0.1')
      ? undefined
      : { rejectUnauthorized: false },
  });
  await client.connect();

  await client.query(`
    create table if not exists schema_migrations (
      filename    text primary key,
      applied_at  timestamptz not null default now()
    );
  `);

  const { rows } = await client.query<{ filename: string }>(
    'select filename from schema_migrations'
  );
  const applied = new Set(rows.map((r) => r.filename));

  const files = readdirSync(MIGRATIONS_DIR)
    .filter((f) => f.endsWith('.sql'))
    .sort();

  let count = 0;
  for (const file of files) {
    if (applied.has(file)) {
      console.log(`  skip  ${file}`);
      continue;
    }
    const sql = readFileSync(join(MIGRATIONS_DIR, file), 'utf8');
    process.stdout.write(`  apply ${file} ... `);
    try {
      // Migrations manage their own begin/commit; wrap only the bookkeeping.
      await client.query(sql);
      await client.query('insert into schema_migrations (filename) values ($1)', [file]);
      console.log('ok');
      count++;
    } catch (err) {
      console.log('FAILED');
      console.error(err instanceof Error ? err.message : err);
      await client.end();
      process.exit(1);
    }
  }

  console.log(count === 0 ? '\nAlready up to date.' : `\nApplied ${count} migration(s).`);
  await client.end();
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
