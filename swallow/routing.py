from channels.routing import ProtocolTypeRouter,URLRouter
from django.conf.urls import url
from operate_record.consumer import AsyncConsumer

application = ProtocolTypeRouter({
    'websocket':URLRouter([
        # websocket��ص�·��
        url(r'^websocket/(?P<room_name>[^/]+)/$', AsyncConsumer),
    ])
})