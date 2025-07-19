# Global Models
# Import all models here to ensure they are available for Alembic migrations

from ..users.models import User
from ..categories.models import Category
from ..expenses.models import Expense, DocumentAnalysis, ExpenseAttachment
from ..business.models import TaxConfiguration