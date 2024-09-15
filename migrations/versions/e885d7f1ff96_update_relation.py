"""Update Relation

Revision ID: e885d7f1ff96
Revises: 9fa8d42b1c54
Create Date: 2024-09-11 15:15:51.356930

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.exc import OperationalError

# revision identifiers, used by Alembic.
revision = 'e885d7f1ff96'
down_revision = '9fa8d42b1c54'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = inspector.get_columns('relation')
    column_names = [c['name'] for c in columns]

    with op.batch_alter_table('relation', schema=None) as batch_op:
        # 步驟 1: 如果 RelationID 列不存在，則添加它
        if 'RelationID' not in column_names:
            batch_op.add_column(sa.Column('RelationID', sa.String(length=50), nullable=True))
        
            # 步驟 2: 為 RelationID 生成唯一值
            op.execute("UPDATE relation SET RelationID = CONCAT(LEAST(UserID1, UserID2), '-', GREATEST(UserID1, UserID2)) WHERE RelationID IS NULL")
        
            # 步驟 3: 將 RelationID 設為非空
            batch_op.alter_column('RelationID', nullable=False)

        # 步驟 4: 為 RelationID 創建唯一索引（如果不存在）
        try:
            batch_op.create_unique_constraint('uq_relation_id', ['RelationID'])
        except OperationalError as e:
            if "Duplicate key name" not in str(e):
                raise
    # ### end Alembic commands ###


def downgrade():
    with op.batch_alter_table('relation', schema=None) as batch_op:
        # 步驟 1: 移除 RelationID 的唯一約束（如果存在）
        try:
            batch_op.drop_constraint('uq_relation_id', type_='unique')
        except OperationalError:
            pass
        
        # 步驟 2: 移除 RelationID 列（如果存在）
        try:
            batch_op.drop_column('RelationID')
        except OperationalError:
            pass

    # ### end Alembic commands ###
