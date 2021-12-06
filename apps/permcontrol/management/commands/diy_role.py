import traceback
from django.core.management.base import BaseCommand
from permcontrol.models import User, PermissionGroup, Role
from core.framework.hashers import make_password

class Command(BaseCommand):

    def handle(self, *args, **options):
        try:
            per_list = []
            permissions = PermissionGroup.objects.filter(id__gt=11)
            for per in permissions:
                per_list.append(per.id)

            role = Role.objects.filter(id=1).first()
            role.permission.add(*per_list)

            self.stdout.write(self.style.SUCCESS('更新权限成功， 权限：{}'.format(per_list)))
        except:
            self.stdout.write(traceback.format_exc())

            self.stdout.write(self.style.ERROR('命令执行出错'))