"""Initial schema — applied via docker-entrypoint-initdb.d.
This migration is a no-op for fresh installs but ensures
Alembic's version table is populated for subsequent migrations."""
from alembic import op

revision = "001"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.execute("SELECT 1")  # Schema already applied by init SQL

def downgrade():
    pass
