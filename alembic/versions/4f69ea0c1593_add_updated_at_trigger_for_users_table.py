"""add updated_at trigger for users table

Revision ID: 4f69ea0c1593
Revises: 6a10a7916097
Create Date: 2025-07-22 21:25:48.842524

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = '4f69ea0c1593'
down_revision = '6a10a7916097'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create trigger function for updating updated_at field
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)

    # Create trigger on users table
    op.execute("""
        CREATE TRIGGER update_users_updated_at
        BEFORE UPDATE ON users
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    """)


def downgrade() -> None:
    # Drop trigger
    op.execute("DROP TRIGGER IF EXISTS update_users_updated_at ON users;")

    # Drop trigger function
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column();")
