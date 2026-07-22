"""fix users, teams, and password column schema drift

Revision ID: 9a1f2b3c4d5e
Revises: 846939560e3d
"""
from alembic import op
import sqlalchemy as sa

revision = "9a1f2b3c4d5e"
down_revision = "846939560e3d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Rename password to hashed_password
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'users' AND column_name = 'password'
            ) THEN
                ALTER TABLE users RENAME COLUMN password TO hashed_password;
            END IF;
        END $$;
    """)

    # 2. Create teams table and add team_id foreign keys
    op.execute("""
        CREATE TABLE IF NOT EXISTS teams (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            manager_id INTEGER REFERENCES users(id),
            created_at TIMESTAMP NOT NULL DEFAULT now()
        );
    """)
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS team_id INTEGER REFERENCES teams(id);")
    op.execute("ALTER TABLE risk_scores ADD COLUMN IF NOT EXISTS team_id INTEGER REFERENCES teams(id);")


def downgrade() -> None:
    op.execute("ALTER TABLE risk_scores DROP COLUMN IF EXISTS team_id;")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS team_id;")
    op.execute("DROP TABLE IF EXISTS teams;")
    op.execute("ALTER TABLE users RENAME COLUMN hashed_password TO password;")