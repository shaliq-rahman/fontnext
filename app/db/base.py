# Import all models to ensure they get registered dynamically on Base
from app.db.database import Base
from app.db.models import User, Font, Customer, Sale

# this allows alembic `target_metadata = Base.metadata` to know about all tables.
