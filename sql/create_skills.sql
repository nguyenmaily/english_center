-- SQL script to create Skills (LR and SW)
-- Table: skills
-- Fields: id (uuid, PK), name (text), description (text), created_at (timestamp), updated_at (timestamp)

-- Insert Listening & Reading (LR) skill
INSERT INTO skills (id, name, description, created_at, updated_at)
VALUES (
    gen_random_uuid(),
    'Listening-Reading',
    'Kỹ năng Listening & Reading - Nghe và Đọc',
    NOW(),
    NOW()
);

-- Insert Speaking & Writing (SW) skill
INSERT INTO skills (id, name, description, created_at, updated_at)
VALUES (
    gen_random_uuid(),
    'Speaking-Writing',
    'Kỹ năng Speaking & Writing - Nói và Viết',
    NOW(),
    NOW()
);

-- Verify inserted skills
SELECT id, name, description, created_at, updated_at
FROM skills
ORDER BY name;

