# AI Companion Modules

from . import consciousness
from . import emotions
from . import memory
from . import knowledge
from . import rewards
from . import thoughts_goals
from . import identity
# Speech is optional - only import if available
try:
    from . import speech
except ImportError:
    pass
from . import llm
from . import virtual_world
from . import metacognition
from . import conversation_style
from . import self_model
from . import attention
from . import active_inference
from . import intrinsic_motivation

