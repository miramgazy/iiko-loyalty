from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0022_organization_smsc_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='organization',
            name='target_payment_type_name',
            field=models.CharField(
                blank=True,
                default='Оплата Бонусами',
                max_length=150,
                verbose_name='Название типа оплаты бонусами в iiko (TargetPaymentTypeName)'
            ),
        ),
    ]

