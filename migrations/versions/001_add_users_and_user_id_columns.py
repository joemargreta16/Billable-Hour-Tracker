"""Add users table and user_id columns to existing tables

Revision ID: 001_add_users_and_user_id_columns
Revises: 
Create Date: 2023-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001_add_users_and_user_id_columns'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create users table
    op.create_table('user',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=80), nullable=False),
        sa.Column('password_hash', sa.String(length=120), nullable=False),
        sa.Column('is_admin', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username')
    )
    
    # Add user_id columns to existing tables
    op.add_column('project', sa.Column('user_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'project', 'user', ['user_id'], ['id'])
    
    op.add_column('time_entry', sa.Column('user_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'time_entry', 'user', ['user_id'], ['id'])


def downgrade():
    # Remove foreign key constraints
    op.drop_constraint(None, 'time_entry', type_='foreignkey')
    op.drop_constraint(None, 'project', type_='foreignkey')
    
    # Remove user_id columns
    op.drop_column('time_entry', 'user_id')
    op.drop_column('project', 'user_id')
    
    # Drop users table
    op.drop_table('user')
