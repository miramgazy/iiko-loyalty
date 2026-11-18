from django.db import migrations

MAP = {
    '7ba81c3a-8de5-8f9d-fb9f-e39efcbc57cc': 'кг',
    'cd19b5ea-1b32-a6e5-1df7-5d2784a0549a': 'шт',
    '6040d92d-e286-f4f9-a613-ed0e6fd241e1': 'порц',
    '69859c74-db72-b006-cba5-326cf6f4fc6e': 'л',
    'b003f902-de36-c128-019f-7e1d6ef2280b': 'услуга',
    'b003f902-de36-c128-019f-7e1d6ef228b2': 'м',
    'b003f902-de36-c128-019f-7e1d6ef22a4a': 'пара',
}

def fix_units(apps, schema_editor):
    InvoiceItem = apps.get_model('invoices', 'InvoiceItem')
    IikoProductEmbedding = apps.get_model('invoices', 'IikoProductEmbedding')

    for it in InvoiceItem.objects.all():
        u = (it.iiko_product_unit or '').strip().lower()
        if u in MAP:
            it.iiko_product_unit = MAP[u]
            it.save(update_fields=['iiko_product_unit'])
        elif len(u) == 36 and u.count('-') == 4:
            it.iiko_product_unit = 'шт'
            it.save(update_fields=['iiko_product_unit'])

    for emb in IikoProductEmbedding.objects.all():
        u = (emb.unit or '').strip().lower()
        if u in MAP:
            emb.unit = MAP[u]
            emb.save(update_fields=['unit'])
        elif len(u) == 36 and u.count('-') == 4:
            emb.unit = 'шт'
            emb.save(update_fields=['unit'])

def noop(apps, schema_editor):
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('invoices', '0005_invoiceitem_iiko_product_unit'),
    ]

    operations = [
        migrations.RunPython(fix_units, noop),
    ]
