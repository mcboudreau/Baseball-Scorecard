"""create core tables

Revision ID: 0001_core
Revises: 
Create Date: 2025-08-31

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001_core'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table('seasons',
        sa.Column('id', sa.BigInteger(), primary_key=True),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_table('teams',
        sa.Column('id', sa.BigInteger(), primary_key=True),
        sa.Column('season_id', sa.BigInteger(), sa.ForeignKey('seasons.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(length=120), nullable=False),
    )
    op.create_index('ix_teams_season_id', 'teams', ['season_id'])
    op.create_index('ix_teams_name', 'teams', ['name'])

    op.create_table('players',
        sa.Column('id', sa.BigInteger(), primary_key=True),
        sa.Column('team_id', sa.BigInteger(), sa.ForeignKey('teams.id', ondelete='CASCADE'), nullable=False),
        sa.Column('first_name', sa.String(length=80), nullable=False),
        sa.Column('last_name', sa.String(length=80), nullable=False),
        sa.Column('handedness', sa.String(length=2), nullable=True),
    )
    op.create_index('ix_players_team_id', 'players', ['team_id'])

    op.create_table('games',
        sa.Column('id', sa.BigInteger(), primary_key=True),
        sa.Column('season_id', sa.BigInteger(), sa.ForeignKey('seasons.id', ondelete='CASCADE'), nullable=False),
        sa.Column('home_team_id', sa.BigInteger(), sa.ForeignKey('teams.id'), nullable=False),
        sa.Column('away_team_id', sa.BigInteger(), sa.ForeignKey('teams.id'), nullable=False),
        sa.Column('start_time', sa.DateTime(), nullable=True),
        sa.Column('status', sa.Enum('live', 'final', name='gamestatus'), nullable=False, server_default='live'),
    )
    op.create_index('ix_games_season_id', 'games', ['season_id'])

    op.create_table('lineups',
        sa.Column('id', sa.BigInteger(), primary_key=True),
        sa.Column('game_id', sa.BigInteger(), sa.ForeignKey('games.id', ondelete='CASCADE'), nullable=False),
        sa.Column('team_id', sa.BigInteger(), sa.ForeignKey('teams.id', ondelete='CASCADE'), nullable=False),
        sa.Column('batting_order', sa.Integer(), nullable=False),
        sa.Column('player_id', sa.BigInteger(), sa.ForeignKey('players.id', ondelete='CASCADE'), nullable=False),
        sa.Column('defensive_position', sa.String(length=3), nullable=True),
        sa.UniqueConstraint('game_id','team_id','batting_order', name='uq_lineup_order'),
    )
    op.create_check_constraint('ck_batting_order_range', 'lineups', 'batting_order BETWEEN 1 AND 9')

    op.create_table('plate_appearances',
        sa.Column('id', sa.BigInteger(), primary_key=True),
        sa.Column('game_id', sa.BigInteger(), sa.ForeignKey('games.id', ondelete='CASCADE'), nullable=False),
        sa.Column('inning', sa.Integer(), nullable=False),
        sa.Column('half', sa.Enum('top', 'bottom', name='halfinning'), nullable=False),
        sa.Column('batter_id', sa.BigInteger(), sa.ForeignKey('players.id'), nullable=False),
        sa.Column('pitcher_id', sa.BigInteger(), sa.ForeignKey('players.id'), nullable=True),
        sa.Column('result', sa.Enum('1B','2B','3B','HR','BB','HBP','K','SF','OUT', name='paresult'), nullable=False),
        sa.Column('rbis', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('notes', sa.String(length=250), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_pa_game_id', 'plate_appearances', ['game_id'])

def downgrade() -> None:
    op.drop_index('ix_pa_game_id', table_name='plate_appearances')
    op.drop_table('plate_appearances')
    op.drop_constraint('ck_batting_order_range', 'lineups', type_='check')
    op.drop_table('lineups')
    op.drop_index('ix_games_season_id', table_name='games')
    op.drop_table('games')
    op.drop_index('ix_players_team_id', table_name='players')
    op.drop_table('players')
    op.drop_index('ix_teams_name', table_name='teams')
    op.drop_index('ix_teams_season_id', table_name='teams')
    op.drop_table('teams')
    op.drop_table('seasons')
    op.execute("DROP TYPE IF EXISTS gamestatus")
    op.execute("DROP TYPE IF EXISTS halfinning")
    op.execute("DROP TYPE IF EXISTS paresult")
