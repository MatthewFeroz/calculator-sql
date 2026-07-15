-- Step B: Insert records

-- These bcrypt values are hashes of throwaway demonstration passwords.  Real
-- application users are inserted through app.services.users.create_user,
-- which generates a new random salt for every password.
INSERT INTO users (username, email, password_hash)
VALUES
('alice', 'alice@example.com', '$2b$12$xJk1nGdDya2KKmM9WloS.uGfyY23iW6J1r7VfJzYoCn2Uhwg5O2X2'),
('bob', 'bob@example.com', '$2b$12$4LrX9MtuEbVDZ9A0AEH8wueZs0JMQ7uQpAA9CT1.iSCi6YqvWNAHi');

INSERT INTO calculations (operation, operand_a, operand_b, result, user_id)
VALUES
('add', 2, 3, 5, 1),
('divide', 10, 2, 5, 1),
('multiply', 4, 5, 20, 2);
