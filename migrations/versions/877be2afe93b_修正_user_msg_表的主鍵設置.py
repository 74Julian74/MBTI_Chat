"""修正 user_msg 表的主鍵設置

Revision ID: 877be2afe93b
Revises: df6977f3847a
Create Date: 2024-08-23 14:44:27.074829

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '877be2afe93b'
down_revision = 'df6977f3847a'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    # 檢查表的當前結構
    columns = inspector.get_columns('user_msg')
    column_names = [col['name'] for col in columns]
    
    with op.batch_alter_table('user_msg') as batch_op:
        # 1. 如果 GroupID 是主鍵或自動遞增，先移除這些屬性
        if 'GroupID' in column_names:
            batch_op.alter_column('GroupID',
                                  existing_type=sa.Integer(),
                                  type_=sa.String(50),
                                  existing_nullable=False,
                                  autoincrement=False)
        
        # 2. 移除現有的主鍵約束（如果存在）
        pk_constraint = inspector.get_pk_constraint('user_msg')
        if pk_constraint and pk_constraint['name']:
            batch_op.drop_constraint(pk_constraint['name'], type_='primary')
        
        # 3. 處理 MessageID 列
        if 'MessageID' not in column_names:
            batch_op.add_column(sa.Column('MessageID', sa.Integer(), nullable=False))
        
        # 4. 設置 MessageID 為主鍵和自動遞增
        batch_op.alter_column('MessageID',
                              existing_type=sa.Integer(),
                              nullable=False,
                              autoincrement=True)
        batch_op.create_primary_key('pk_user_msg', ['MessageID'])
        
        # 5. 為 GroupID 創建索引（如果需要）
        indexes = [idx['name'] for idx in inspector.get_indexes('user_msg')]
        if 'ix_user_msg_GroupID' not in indexes:
            batch_op.create_index('ix_user_msg_GroupID', ['GroupID'])
        
        # 6. 修改其他列（如果需要）
        if 'ChatContentID' in column_names:
            batch_op.alter_column('ChatContentID',
                                  existing_type=sa.String(255),
                                  type_=sa.String(500),
                                  existing_nullable=False)
        if 'Emotion' in column_names:
            batch_op.alter_column('Emotion',
                                  existing_type=sa.String(255),
                                  type_=sa.String(20),
                                  existing_nullable=False)

def downgrade():
    # 實現降級邏輯（如果需要）
    with op.batch_alter_table('user_msg') as batch_op:
        # 1. 移除 MessageID 的主鍵
        batch_op.drop_constraint('pk_user_msg', type_='primary')
        
        # 2. 將 GroupID 改回 Integer 並設為主鍵
        batch_op.alter_column('GroupID',
                              type_=sa.Integer(),
                              existing_type=sa.String(50),
                              autoincrement=True,
                              nullable=False)
        batch_op.create_primary_key('pk_user_msg', ['GroupID'])
        
        # 3. 移除 MessageID 列（如果它是新添加的）
        batch_op.drop_column('MessageID')
        
        # 4. 恢復其他列的原始類型
        batch_op.alter_column('ChatContentID',
                              type_=sa.String(255),
                              existing_type=sa.String(500),
                              existing_nullable=False)
        batch_op.alter_column('Emotion',
                              type_=sa.String(255),
                              existing_type=sa.String(20),
                              existing_nullable=False)

    # ### end Alembic commands ###
