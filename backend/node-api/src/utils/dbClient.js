import pg from 'pg';
import 'dotenv/config';

const { Pool } = pg;

// Initialize and export the PostgreSQL connection pool.
// The pool will automatically use the DATABASE_URL environment variable.
const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
});

export default pool;
