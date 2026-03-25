"""IRG Auto Translate module

Minimal implementation: adds translation support for `op.subject` and a
paginated wizard + cron skeleton to run batched translations. External
provider integration is left as a TODO and controlled by system params.
"""
from . import models
from . import wizard

__all__ = ["models", "wizard"]
from . import models
