from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework.schemas import get_schema_view
from rest_framework_simplejwt.views import TokenRefreshView

from accounts.views import MeView, RegisterView, CareBridgeTokenObtainPairView
from config.api_views import DashboardSummaryView
from patients.views import PatientViewSet
from doctors.views import DoctorViewSet, DoctorAvailabilityViewSet
from appointments.views import AppointmentViewSet
from prescriptions.views import PrescriptionViewSet
from billing.views import InvoiceViewSet, PaymentViewSet

router = DefaultRouter()
router.register("patients", PatientViewSet, basename="patient")
router.register("doctors", DoctorViewSet, basename="doctor")
router.register("availabilities", DoctorAvailabilityViewSet, basename="availability")
router.register("appointments", AppointmentViewSet, basename="appointment")
router.register("prescriptions", PrescriptionViewSet, basename="prescription")
router.register("invoices", InvoiceViewSet, basename="invoice")
router.register("payments", PaymentViewSet, basename="payment")


def health_check(request):
    return JsonResponse({"application": "CareBridge API", "status": "ok"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health_check, name="health-check"),
    path("api/dashboard/summary/", DashboardSummaryView.as_view(), name="dashboard-summary"),
    path("api/auth/register/", RegisterView.as_view(), name="auth-register"),
    path("api/auth/token/", CareBridgeTokenObtainPairView.as_view(), name="token-obtain-pair"),
    path("api/auth/token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("api/auth/me/", MeView.as_view(), name="auth-me"),
    path("api/schema/", get_schema_view(title="CareBridge API", version="1.0.0"), name="openapi-schema"),
    path("api/", include(router.urls)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
