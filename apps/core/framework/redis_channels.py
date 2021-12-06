import time
import json
from channels_redis.core import RedisChannelLayer
from config.config import CommonConfig
from channels.exceptions import ChannelFull

import logging

logger = logging.getLogger("django")

class CommonRedisChannelLayer(RedisChannelLayer):
    async def notify_apply(self):
        channel_names = []
        message = ""
        cache_key = CommonConfig.consumer_key
        pool = await self.connection(self.consistent_hash(cache_key))
        with (await pool) as connection:
            result = await connection.rpop(cache_key)
            if result:
                message = json.loads(str(result, 'utf-8'))
                key = self._group_key('notice_user_{}'.format(message['user_id']),)
                channel_names = [
                    x.decode("utf8") for x in
                    await connection.zrange(key, 0, -1)
                ]
        if message and len(channel_names) > 0:
            for channel in channel_names:
                data = {
                    "type": "system_message",
                    "message": message,
                }
                try:
                    await self.send(channel, data)
                except ChannelFull:
                    pass

    '''
    websocket保持连接状态，但是redis group_name ttl
    导致消息推送成功，但是接收不到
    '''
    async def group_delay(self, group, channel):
        """
        Adds the channel name to a group.
        """
        # Check the inputs
        assert self.valid_group_name(group), "Group name not valid"
        assert self.valid_channel_name(channel), "Channel name not valid"
        # Get a connection to the right shard
        group_key = self._group_key(group)
        pool = await self.connection(self.consistent_hash(group))
        with (await pool) as connection:
            is_exist = await connection.exists(group_key)
            if is_exist == 1:
                await connection.zremrangebyscore(group_key, min=0, max=int(time.time()) - self.group_expiry)
                score = await connection.zscore(group_key, channel)
                if not score:
                    await connection.zadd(
                        group_key,
                        time.time(),
                        channel,
                    )
                await connection.expire(group_key, self.group_expiry)
            else:
                await connection.zadd(
                    group_key,
                    time.time(),
                    channel,
                )
                await connection.expire(group_key, self.group_expiry)

            try:
                data = {
                    'type': 'system_message',
                    'message': {
                        "message": "pong"
                    }
                }
                await self.send(channel, data)
            except ChannelFull:
                pass


