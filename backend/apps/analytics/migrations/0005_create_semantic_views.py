from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('analytics', '0004_alter_iikoolappreset_report_type_key'),
        ('inventory', '0001_initial'),
    ]

    operations = [
        # 1. v_ai_daily_sales
        migrations.RunSQL(
            sql="""
                DROP VIEW IF EXISTS v_ai_daily_sales;
                CREATE VIEW v_ai_daily_sales AS 
                SELECT organization_id, date, revenue, cost, discounts, checks_count, guests_count 
                FROM analytics_dailyolapreport;
            """,
            reverse_sql="DROP VIEW IF EXISTS v_ai_daily_sales;"
        ),
        # 2. v_ai_payment_types
        migrations.RunSQL(
            sql="""
                DROP VIEW IF EXISTS v_ai_payment_types;
                CREATE VIEW v_ai_payment_types AS 
                SELECT organization_id, date, payment_type, revenue, checks_count 
                FROM analytics_paymenttypeolapreport;
            """,
            reverse_sql="DROP VIEW IF EXISTS v_ai_payment_types;"
        ),
        # 3. v_ai_stop_list
        migrations.RunSQL(
            sql="""
                DROP VIEW IF EXISTS v_ai_stop_list;
                CREATE VIEW v_ai_stop_list AS 
                SELECT organization_id, product_id, product_name, started_at, ended_at, duration_seconds, lost_revenue, lost_profit 
                FROM inventory_stoplisthistory;
            """,
            reverse_sql="DROP VIEW IF EXISTS v_ai_stop_list;"
        ),
        # 4. v_ai_product_purchases
        migrations.RunSQL(
            sql="""
                DROP VIEW IF EXISTS v_ai_product_purchases;
                CREATE VIEW v_ai_product_purchases AS 
                SELECT organization_id, product_id, product_name, supplier_name, price, quantity, date 
                FROM inventory_productpurchasehistory;
            """,
            reverse_sql="DROP VIEW IF EXISTS v_ai_product_purchases;"
        ),
    ]
