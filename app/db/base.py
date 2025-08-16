# Import all the models, so that Base has them before being
# imported by Alembic
from app.db.base_class import Base  # noqa
from app.models.user import User  # noqa
from app.models.project import Project  # noqa
from app.models.wip_snapshot import WIPSnapshot  # noqa
from app.models.explanation import CellExplanation  # noqa
from app.models.audit_log import AuditLog  # noqa
