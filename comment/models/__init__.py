from comment.models.comments import Comment
from comment.models.reactions import Reaction, ReactionInstance
from comment.models.flags import Flag, FlagInstance
from comment.models.followers import Follower
from comment.models.blocker import BlockedUser, BlockedUserHistory
from comment.managers import (
    CommentManager, ReactionManager, ReactionInstanceManager, FlagManager, FlagInstanceManager, FollowerManager,
    BlockedUserManager, BlockedUserHistoryManager,
    )

__all__ = (
    'Comment',
    'Reaction',
    'ReactionInstance',
    'Flag',
    'FlagInstance',
    'Follower',
    'BlockedUser',
    'BlockedUserHistory',
    # TODO: managers are given here due to the earlier namespace pollutin caused by star imports,
    # remove these along with their imports in v3.0.0
    'CommentManager',
    'ReactionManager',
    'ReactionInstanceManager',
    'FlagManager',
    'FlagInstanceManager',
    'FollowerManager',
    'BlockedUserManager',
    'BlockedUserHistoryManager',
)
