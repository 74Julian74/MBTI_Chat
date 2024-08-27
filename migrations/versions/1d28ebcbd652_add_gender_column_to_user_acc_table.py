"""Add gender column to user_acc table

Revision ID: 1d28ebcbd652
Revises: 
Create Date: 2024-08-19 11:58:18.353623

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '1d28ebcbd652'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_index('email')

    op.drop_table('users')
    op.drop_table('message')
    with op.batch_alter_table('relation', schema=None) as batch_op:
        batch_op.alter_column('Status',
               existing_type=mysql.TINYINT(display_width=1),
               type_=sa.String(length=20),
               existing_nullable=False)

    with op.batch_alter_table('user_acc', schema=None) as batch_op:
        batch_op.add_column(sa.Column('gender', sa.String(length=5), nullable=True))
        batch_op.alter_column('username',
               existing_type=mysql.VARCHAR(length=20),
               nullable=True)
        batch_op.alter_column('password',
               existing_type=mysql.VARCHAR(length=60),
               type_=sa.String(length=255),
               existing_nullable=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user_acc', schema=None) as batch_op:
        batch_op.alter_column('password',
               existing_type=sa.String(length=255),
               type_=mysql.VARCHAR(length=60),
               existing_nullable=False)
        batch_op.alter_column('username',
               existing_type=mysql.VARCHAR(length=20),
               nullable=False)
        batch_op.drop_column('gender')

    with op.batch_alter_table('relation', schema=None) as batch_op:
        batch_op.alter_column('Status',
               existing_type=sa.String(length=20),
               type_=mysql.TINYINT(display_width=1),
               existing_nullable=False)

    op.create_table('message',
    sa.Column('id', mysql.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('username', mysql.VARCHAR(length=50), nullable=False),
    sa.Column('text', mysql.VARCHAR(length=200), nullable=False),
    sa.Column('timestamp', mysql.DATETIME(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    mysql_collate='utf8mb4_0900_ai_ci',
    mysql_default_charset='utf8mb4',
    mysql_engine='InnoDB'
    )
    op.create_table('users',
    sa.Column('id', mysql.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('username', mysql.VARCHAR(length=150), nullable=False),
    sa.Column('email', mysql.VARCHAR(length=150), nullable=False),
    sa.Column('password_hash', mysql.VARCHAR(length=256), nullable=False),
    sa.Column('mbti', mysql.VARCHAR(length=4), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    mysql_collate='utf8mb4_0900_ai_ci',
    mysql_default_charset='utf8mb4',
    mysql_engine='InnoDB'
    )
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.create_index('email', ['email'], unique=True)

    # ### end Alembic commands ###
