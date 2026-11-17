from django.core.management.base import BaseCommand
from apps.core.models import Organization
from apps.invoices.tasks import sync_and_vectorize_organization_task


class Command(BaseCommand):
    help = "Синхронизирует отфильтрованную номенклатуру iiko и вычисляет векторные эмбеддинги (pgvector)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--org-id",
            type=int,
            help="ID организации для векторизации (если не указано, обрабатываются все активные)",
        )
        parser.add_argument(
            "--all",
            action="store_true",
            help="Обработать все активные организации с включенным модулем накладных",
        )

    def handle(self, *args, **options):
        org_id = options.get("org_id")
        process_all = options.get("all")

        if org_id:
            orgs = Organization.objects.filter(id=org_id)
        elif process_all:
            orgs = Organization.objects.filter(is_active=True, is_invoices_enabled=True)
        else:
            self.stdout.write(self.style.WARNING("Укажите --org-id=<id> или --all"))
            return

        if not orgs.exists():
            self.stdout.write(self.style.ERROR("Организации не найдены"))
            return

        for org in orgs:
            self.stdout.write(f"Запуск синхронизации и векторизации для: {org.name} (ID: {org.id})...")
            sync_and_vectorize_organization_task(org.id)
            self.stdout.write(self.style.SUCCESS(f"Завершено для: {org.name}"))
