from django.urls import path

from . import views


urlpatterns = [
    path('', views.TraceChallengeListView.as_view(), name='trace_challenges'),
    path('<slug:slug>/', views.TraceChallengeView.as_view(), name='trace_challenge'),
    path('<slug:slug>/state/', views.TraceStateListView.as_view(), name='trace_state_list'),
]
