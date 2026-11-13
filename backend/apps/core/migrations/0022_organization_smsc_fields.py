from django.db import migrations, models
import apps.core.fields


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0021_organization_is_bonus_confirmation_enabled_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='organization',
            name='is_smsc_enabled',
            field=models.BooleanField(default=False, verbose_name='Включена отправка через SMS-Центр (SMSC)'),
        ),
        migrations.AddField(
            model_name='organization',
            name='smsc_login',
            field=models.CharField(blank=True, default='', max_length=128, verbose_name='SMSC Логин'),
        ),
        migrations.AddField(
            model_name='organization',
            name='smsc_password',
            field=apps.core.fields.EncryptedCharField(blank=True, max_length=128, null=True, verbose_name='SMSC Пароль / API Ключ'),
        ),
        migrations.AddField(
            model_name='organization',
            name='smsc_sender',
            field=models.CharField(blank=True, default='', max_length=64, verbose_name='SMSC Имя отправителя (Sender)'),
        ),
    ]

