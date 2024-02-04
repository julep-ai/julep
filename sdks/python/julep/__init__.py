from beartype.roar import BeartypeDecorHintPep585DeprecationWarning
from warnings import filterwarnings

filterwarnings("ignore", category=BeartypeDecorHintPep585DeprecationWarning)

### Import code below the warning filter ###

from .client import Client, AsyncClient  # noqa: F401, E402

__all__ = ["Client", "AsyncClient"]
