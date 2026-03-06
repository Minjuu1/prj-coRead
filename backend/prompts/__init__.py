from .pipeline.annotation import get_annotation_prompt
from .pipeline.cross_reading import get_cross_reading_prompt
from .pipeline.discussion import get_discussion_prompt, get_comment_prompt

__all__ = [
    'get_annotation_prompt',
    'get_cross_reading_prompt',
    'get_discussion_prompt',
    'get_comment_prompt',
]
