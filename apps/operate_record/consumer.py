from channels.generic.websocket import AsyncWebsocketConsumer

import json
import logging

logger = logging.getLogger("django")

class AsyncConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # 连接时触发
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        # 直接从用户指定的房间名称构造Channels组名称，不进行任何引用或转义。
        self.room_group_name = 'notice_%s' % self.room_name
        # 将新的连接加入到群组
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):  # 断开时触发
        # 将关闭的连接从群组中移除
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data=None, bytes_data=None):  # 接收消息时触发
        if text_data == 'ping':
            # delay
            logger.info("delay group:{}  channel:{}".format(self.room_group_name, self.channel_name))
            await self.channel_layer.group_delay(self.room_group_name, self.channel_name)



    # Receive message from room group
    async def system_message(self, event):
        message = event['message']
        logger.info("{}_{}  send system_message {}".format(self.room_group_name, self.channel_name, message))
        # Send message to WebSocket单发消息
        await self.send(text_data=json.dumps(message, ensure_ascii=False))

