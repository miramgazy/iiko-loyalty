from rest_framework import serializers
from apps.analytics.models import IikoOlapPreset

class IikoOlapPresetSerializer(serializers.ModelSerializer):
    class Meta:
        model = IikoOlapPreset
        fields = ['id', 'report_type_key', 'name', 'description', 'preset_id', 'is_system', 'created_at', 'updated_at']
        read_only_fields = ['id', 'is_system', 'created_at', 'updated_at']

    def validate_report_type_key(self, value):
        # We don't allow users to manually set system keys
        if value in ['daily_kpi', 'hourly_sales'] and not self.instance:
            raise serializers.ValidationError("Нельзя вручную создавать системные отчеты.")
        return value
