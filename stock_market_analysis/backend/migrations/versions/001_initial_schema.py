"""initial production schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-10-04 18:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Stocks table
    op.create_table(
        'stocks',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('symbol', sa.String(length=30), nullable=False),
        sa.Column('company_name', sa.String(length=255), nullable=False),
        sa.Column('exchange', sa.String(length=10), server_default='NSE', nullable=False),
        sa.Column('sector', sa.String(length=100), nullable=True),
        sa.Column('industry', sa.String(length=100), nullable=True),
        sa.Column('isin', sa.String(length=20), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('isin', name='uq_stocks_isin'),
        sa.UniqueConstraint('symbol', name='uq_stocks_symbol')
    )
    op.create_index('idx_stocks_symbol', 'stocks', ['symbol'])
    op.create_index('idx_stocks_exchange_active', 'stocks', ['exchange', 'is_active'])

    # 2. Historical Market Data table
    op.create_table(
        'market_data',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('stock_id', sa.Integer(), nullable=False),
        sa.Column('trading_date', sa.Date(), nullable=False),
        sa.Column('open', sa.Numeric(precision=14, scale=4), nullable=False),
        sa.Column('high', sa.Numeric(precision=14, scale=4), nullable=False),
        sa.Column('low', sa.Numeric(precision=14, scale=4), nullable=False),
        sa.Column('close', sa.Numeric(precision=14, scale=4), nullable=False),
        sa.Column('adj_close', sa.Numeric(precision=14, scale=4), nullable=False),
        sa.Column('volume', sa.BigInteger(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['stock_id'], ['stocks.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('stock_id', 'trading_date', name='uq_stock_trading_date')
    )
    op.create_index('idx_market_data_stock_date_desc', 'market_data', ['stock_id', sa.text('trading_date DESC')])
    op.create_index('idx_market_data_date_desc', 'market_data', [sa.text('trading_date DESC')])

    # 3. Fundamentals table
    op.create_table(
        'fundamentals',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('stock_id', sa.Integer(), nullable=False),
        sa.Column('as_of_date', sa.Date(), nullable=False),
        sa.Column('revenue_growth_pct', sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column('profit_growth_pct', sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column('eps_trailing', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('eps_forward', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('pe_ratio', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('pb_ratio', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('roe_pct', sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column('roce_pct', sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column('debt_to_equity', sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column('free_cash_flow', sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column('promoter_holding_pct', sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column('institutional_holding_pct', sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column('fundamental_score', sa.Integer(), nullable=True),
        sa.Column('fundamental_rating', sa.String(length=50), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('key_highlights', sa.JSON(), nullable=True),
        sa.Column('raw_metrics', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint('fundamental_score >= 0 AND fundamental_score <= 100', name='chk_fundamental_score_range'),
        sa.ForeignKeyConstraint(['stock_id'], ['stocks.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('stock_id', 'as_of_date', name='uq_stock_fundamental_date')
    )
    op.create_index('idx_fundamentals_stock_date_desc', 'fundamentals', ['stock_id', sa.text('as_of_date DESC')])

    # 4. Analysis Snapshots table
    op.create_table(
        'analysis_snapshots',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('stock_id', sa.Integer(), nullable=False),
        sa.Column('analysis_date', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('period', sa.String(length=10), server_default='1y', nullable=False),
        sa.Column('latest_price', sa.Numeric(precision=14, scale=4), nullable=False),
        sa.Column('trend_classification', sa.String(length=50), nullable=True),
        sa.Column('trend_score', sa.Integer(), nullable=True),
        sa.Column('ma20_slope', sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column('ml_bullish_prob_pct', sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column('ml_prediction', sa.String(length=20), nullable=True),
        sa.Column('ml_confidence', sa.String(length=20), nullable=True),
        sa.Column('ml_metrics', sa.JSON(), nullable=True),
        sa.Column('feature_importances', sa.JSON(), nullable=True),
        sa.Column('indicator_summary', sa.JSON(), nullable=True),
        sa.Column('backtest_summary', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['stock_id'], ['stocks.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_analysis_stock_date_desc', 'analysis_snapshots', ['stock_id', sa.text('analysis_date DESC')])

    # 5. Trading Signals table
    op.create_table(
        'trading_signals',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('stock_id', sa.Integer(), nullable=False),
        sa.Column('analysis_id', sa.BigInteger(), nullable=True),
        sa.Column('signal_date', sa.Date(), nullable=False),
        sa.Column('signal_type', sa.String(length=20), nullable=False),
        sa.Column('confidence_score', sa.Integer(), nullable=True),
        sa.Column('technical_score', sa.Integer(), nullable=True),
        sa.Column('fundamental_score', sa.Integer(), nullable=True),
        sa.Column('risk_score', sa.Integer(), nullable=True),
        sa.Column('risk_level', sa.String(length=30), nullable=True),
        sa.Column('entry_price', sa.Numeric(precision=14, scale=4), nullable=False),
        sa.Column('stop_loss', sa.Numeric(precision=14, scale=4), nullable=False),
        sa.Column('target_price', sa.Numeric(precision=14, scale=4), nullable=False),
        sa.Column('risk_reward_ratio', sa.String(length=20), nullable=True),
        sa.Column('expected_time_horizon', sa.String(length=100), nullable=True),
        sa.Column('pros', sa.JSON(), nullable=True),
        sa.Column('cons', sa.JSON(), nullable=True),
        sa.Column('risks', sa.JSON(), nullable=True),
        sa.Column('reason_for_decision', sa.Text(), nullable=True),
        sa.Column('ai_explanation', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint('confidence_score >= 0 AND confidence_score <= 100', name='chk_signal_confidence_range'),
        sa.ForeignKeyConstraint(['analysis_id'], ['analysis_snapshots.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['stock_id'], ['stocks.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_signals_stock_date_desc', 'trading_signals', ['stock_id', sa.text('signal_date DESC')])
    op.create_index('idx_signals_type_date_desc', 'trading_signals', ['signal_type', sa.text('signal_date DESC')])

    # 6. Risk Assessments table
    op.create_table(
        'risk_assessments',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('stock_id', sa.Integer(), nullable=False),
        sa.Column('analysis_id', sa.BigInteger(), nullable=True),
        sa.Column('assessment_date', sa.Date(), nullable=False),
        sa.Column('risk_score', sa.Integer(), nullable=True),
        sa.Column('risk_category', sa.String(length=30), nullable=True),
        sa.Column('annualized_volatility_pct', sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column('suggested_entry_price', sa.Numeric(precision=14, scale=4), nullable=True),
        sa.Column('suggested_stop_loss', sa.Numeric(precision=14, scale=4), nullable=True),
        sa.Column('suggested_target_price', sa.Numeric(precision=14, scale=4), nullable=True),
        sa.Column('risk_to_reward_ratio', sa.String(length=20), nullable=True),
        sa.Column('recommended_shares', sa.Integer(), nullable=True),
        sa.Column('suggested_position_value', sa.Numeric(precision=14, scale=4), nullable=True),
        sa.Column('suggested_portfolio_pct', sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint('risk_score >= 0 AND risk_score <= 100', name='chk_risk_score_range'),
        sa.ForeignKeyConstraint(['analysis_id'], ['analysis_snapshots.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['stock_id'], ['stocks.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_risk_stock_date_desc', 'risk_assessments', ['stock_id', sa.text('assessment_date DESC')])

    # 7. AI Research Logs table
    op.create_table(
        'ai_research_logs',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('stock_id', sa.Integer(), nullable=True),
        sa.Column('raw_query', sa.Text(), nullable=False),
        sa.Column('interpreted_symbol', sa.String(length=30), nullable=True),
        sa.Column('interpreted_intent', sa.String(length=100), nullable=True),
        sa.Column('timeframe', sa.String(length=50), nullable=True),
        sa.Column('peers', sa.JSON(), nullable=True),
        sa.Column('research_plan', sa.JSON(), nullable=True),
        sa.Column('agent_type', sa.String(length=50), nullable=True),
        sa.Column('ai_response', sa.Text(), nullable=False),
        sa.Column('context_data', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['stock_id'], ['stocks.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_ai_research_stock_desc', 'ai_research_logs', ['stock_id', sa.text('created_at DESC')])
    op.create_index('idx_ai_research_created_desc', 'ai_research_logs', [sa.text('created_at DESC')])


def downgrade() -> None:
    op.drop_table('ai_research_logs')
    op.drop_table('risk_assessments')
    op.drop_table('trading_signals')
    op.drop_table('analysis_snapshots')
    op.drop_table('fundamentals')
    op.drop_table('market_data')
    op.drop_table('stocks')
