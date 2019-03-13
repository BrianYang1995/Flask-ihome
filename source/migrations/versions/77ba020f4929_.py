"""empty message

Revision ID: 77ba020f4929
Revises: 06a65edde4be
Create Date: 2018-08-25 16:20:02.248180

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '77ba020f4929'
down_revision = '06a65edde4be'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('ih_house_info', sa.Column('user_id', sa.Integer(), nullable=False))
    op.drop_constraint(u'ih_house_info_ibfk_2', 'ih_house_info', type_='foreignkey')
    op.create_foreign_key(None, 'ih_house_info', 'ih_user_profile', ['user_id'], ['id'])
    op.drop_column('ih_house_info', 'usr_id')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('ih_house_info', sa.Column('usr_id', mysql.INTEGER(display_width=11), autoincrement=False, nullable=False))
    op.drop_constraint(None, 'ih_house_info', type_='foreignkey')
    op.create_foreign_key(u'ih_house_info_ibfk_2', 'ih_house_info', 'ih_user_profile', ['usr_id'], ['id'])
    op.drop_column('ih_house_info', 'user_id')
    # ### end Alembic commands ###