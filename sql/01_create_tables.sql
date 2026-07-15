-- Step A: Create tables
-- users is the parent table; calculations references it through user_id,
-- forming a one-to-many relationship (one user has many calculations).

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(254) NOT NULL UNIQUE,
    -- Store only a salted one-way hash; never add a plaintext password column.
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE calculations (
    id SERIAL PRIMARY KEY,
    operation VARCHAR(20) NOT NULL,
    operand_a FLOAT NOT NULL,
    operand_b FLOAT NOT NULL,
    result FLOAT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id INTEGER NOT NULL,
    -- ON DELETE CASCADE: deleting a user automatically deletes their calculations.
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
