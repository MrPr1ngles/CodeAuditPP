from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('create-session/', views.create_session_view, name='create_session'),
    path('my-sessions/', views.sessions_list_view, name='sessions_list'),
    path('session/<str:code>/', views.session_detail_view, name='session_detail'),
    path('join-session/', views.join_session_view, name='join_session'),
    path('code-editor/<str:code>/', views.code_editor_view, name='code_editor'),
]
