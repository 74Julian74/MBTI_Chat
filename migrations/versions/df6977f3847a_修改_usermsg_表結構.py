"""修改 UserMSG 表結構

Revision ID: df6977f3847a
Revises: 8251f160f0a1
Create Date: 2024-08-23 14:30:51.444864

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'df6977f3847a'
down_revision = '8251f160f0a1'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('user_msg', schema=None) as batch_op:
        # 移除 GroupID 作為主鍵
        batch_op.drop_constraint('PRIMARY', type_='primary')
        
        # 修改 MessageID 為主鍵
        batch_op.alter_column('MessageID',
               existing_type=mysql.INTEGER(),
               nullable=False,
               autoincrement=True)
        batch_op.create_primary_key('pk_user_msg', ['MessageID'])
        
        # 其他列的修改保持不變
        batch_op.alter_column('GroupID',
               existing_type=mysql.VARCHAR(length=20),
               type_=sa.String(length=50),
               existing_nullable=False)
        batch_op.alter_column('ChatContentID',
               existing_type=mysql.VARCHAR(length=250),
               type_=sa.String(length=500),
               existing_nullable=False)
        batch_op.alter_column('Emotion',
               existing_type=mysql.VARCHAR(length=10),
               type_=sa.String(length=20),
               existing_nullable=False)
        batch_op.create_index(batch_op.f('ix_user_msg_GroupID'), ['GroupID'], unique=False)

def downgrade():
    with op.batch_alter_table('user_msg', schema=None) as batch_op:
        # 恢復 GroupID 作為主鍵
        batch_op.drop_constraint('pk_user_msg', type_='primary')
        batch_op.create_primary_key('PRIMARY', ['GroupID'])
        
        batch_op.drop_index(batch_op.f('ix_user_msg_GroupID'))
        batch_op.alter_column('Emotion',
               existing_type=sa.String(length=20),
               type_=mysql.VARCHAR(length=10),
               existing_nullable=False)
        batch_op.alter_column('ChatContentID',
               existing_type=sa.String(length=500),
               type_=mysql.VARCHAR(length=250),
               existing_nullable=False)
        batch_op.alter_column('GroupID',
               existing_type=sa.String(length=50),
               type_=mysql.VARCHAR(length=20),
               existing_nullable=False)
        batch_op.alter_column('MessageID',
               existing_type=mysql.INTEGER(),
               nullable=True,
               autoincrement=True)

    # ### end Alembic commands ###
