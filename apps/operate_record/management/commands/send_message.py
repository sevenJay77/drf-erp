import traceback
from django.core.management.base import BaseCommand
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument(
            dest='user_id',
            type=str,
            help='用户id',
        )


    def handle(self, *args, **options):
        try:
            user_id = options['user_id']
            # 从Channels的外部发送消息给Channel
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                'notice_user_{}'.format(user_id),  # 构造Channels组名称
                {
                    "type": "system_message",
                    "message": {'data': 111},
                }
            )

            self.stdout.write(self.style.SUCCESS('发送成功'))
        except:
            self.stdout.write(traceback.format_exc())

            self.stdout.write(self.style.ERROR('命令执行出错'))