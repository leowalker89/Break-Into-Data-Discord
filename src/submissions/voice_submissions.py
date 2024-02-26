from datetime import datetime
import logging

from src.database import ensure_user, get_category_for_voice, get_goal, new_submission


logger = logging.getLogger(__name__)


# map from a user to it's voice channel join time
VOICE_CHANNELS_JOIN_TIME = {}


async def process_voice_channel_activity(member, before, after):
    member_joins_channel = before.channel is None and after.channel is not None
    member_leaves_channel = before.channel is not None and (after.channel is None or after.channel.name != before.channel.name)

    user = await ensure_user(member)

    if member_joins_channel:
        VOICE_CHANNELS_JOIN_TIME[user.user_id] = datetime.now(datetime.UTC)
        logger.debug(f'Voice channel activity: {member} joined {after.channel.name}')

    if member_leaves_channel:
        logger.debug(f'Voice channel activity: {member} left {before.channel.name}')
        time_joined = VOICE_CHANNELS_JOIN_TIME.pop(user.user_id, None)
        if time_joined is None:
            return
        
        time_left = datetime.utcnow()
        time_spent = time_left - time_joined

        category = await get_category_for_voice(before.channel.name)
        if category is None:
            return

        goal = await get_goal(category.category_id, user.user_id)
        if goal is None:
            return

        await new_submission(
            user_id=user.user_id,
            goal_id=goal.goal_id,
            proof_url=None,
            amount=time_spent.seconds // 60,
        )
