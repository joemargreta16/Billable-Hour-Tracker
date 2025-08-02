from app import app, db
from alembic import op
import sqlalchemy as sa

with app.app_context():
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
    
    print('Migration applied')
