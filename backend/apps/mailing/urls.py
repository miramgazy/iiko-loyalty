from rest_framework.routers import DefaultRouter
from apps.mailing.views import MailingTaskViewSet

router = DefaultRouter()
router.register(r'', MailingTaskViewSet, basename='mailing')

urlpatterns = router.urls
