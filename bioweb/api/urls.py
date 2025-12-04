from django.urls import path
from . import views

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)



urlpatterns = [
    path('',views.getRoutes),
    path('users/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('users/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('users/register/',views.register,name="register"),
    path("predict/", views.predict_gene, name="predict_gene"),
    path('result/<str:pk>/', views.get_gene_prediction_result, name='get_gene_prediction_result'),
    path("blast/<str:gene_id>/", views.blast_gene),
]
