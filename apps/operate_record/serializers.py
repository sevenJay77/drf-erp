from rest_framework import serializers
from operate_record.models import AdminOperateRecord,  NotifyMessage



class AdminOperateRecordSerializer(serializers.ModelSerializer):
    created_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)

    class Meta:
        model = AdminOperateRecord
        fields = ['comment', 'user_id', 'created_time']



class AdminNotifyRecordSerializer(serializers.ModelSerializer):
    created_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)
    updated_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)

    class Meta:
        model = AdminOperateRecord
        fields = '__all__'



class AdminNotifySerializer(serializers.Serializer):
    title = serializers.CharField(required=True, error_messages={"required": "请输入标题", "blank": "标题不能为空", "null": "标题不能为空"})
    module = serializers.CharField(required=True, allow_null=True, allow_blank=True, error_messages={"required": "请输入模块"})
    record_sign = serializers.CharField(required=True, allow_null=True, allow_blank=True, error_messages={"required": "请输入主键"})
    user_list = serializers.CharField(required=False, allow_null=True, allow_blank=True)



class NotifyMessageSerializer(serializers.ModelSerializer):
    created_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)
    updated_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)

    class Meta:
        model = NotifyMessage
        fields = '__all__'