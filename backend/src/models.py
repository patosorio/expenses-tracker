# Global Models
# Import all models here to ensure they are available for Alembic migrations

from src.users.models import User
from src.categories.models import Category
from src.expenses.models import Expense, DocumentAnalysis, ExpenseAttachment
from src.business.models import TaxConfiguration