import logging
from datetime import date, timedelta, datetime
from django.core.management.base import BaseCommand
from apps.core.models import Organization
from apps.analytics.services import sync_daily_olap_for_date, sync_hourly_olap_for_date

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Синхронизирует исторические данные OLAP отчетов из iiko Server для организаций."

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=31,
            help="Количество прошедших дней для синхронизации (по умолчанию 31 день, чтобы заполнить KPI сравнения)",
        )
        parser.add_argument(
            "--org-id",
            type=int,
            help="Идентификатор конкретной организации для синхронизации",
        )

    def handle(self, *args, **options):
        days = options["days"]
        org_id = options["org_id"]

        today = date.today()
        start_date = today - timedelta(days=days)
        end_date = today

        # Fetch organizations
        if org_id:
            orgs = Organization.objects.filter(id=org_id, is_active=True, is_analytics_enabled=True)
        else:
            orgs = Organization.objects.filter(is_active=True, is_analytics_enabled=True)

        if not orgs.exists():
            self.stdout.write(self.style.WARNING("Нет активных организаций с включенным модулем аналитики."))
            return

        self.stdout.write(
            self.style.SUCCESS(
                f"Начало синхронизации OLAP за период с {start_date} по {end_date} ({days} дней) для {orgs.count()} орг."
            )
        )

        for org in orgs:
            self.stdout.write(self.style.MIGRATE_HEADING(f"Синхронизация для организации: {org.name} (ID: {org.id})"))
            
            # Loop day-by-day
            current_date = start_date
            success_count = 0
            fail_count = 0

            while current_date <= end_date:
                self.stdout.write(f"  Синхронизация даты {current_date}... ", ending="")
                try:
                    # Sync daily numbers
                    sync_daily_olap_for_date(org, current_date)
                    # Sync hourly sales details
                    sync_hourly_olap_for_date(org, current_date)
                    
                    self.stdout.write(self.style.SUCCESS("ОК"))
                    success_count += 1
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"ОШИБКА: {e}"))
                    fail_count += 1
                
                current_date += timedelta(days=1)

            self.stdout.write(
                self.style.SUCCESS(
                    f"Завершена синхронизация для {org.name}: {success_count} дней успешно, {fail_count} ошибок."
                )
            )
