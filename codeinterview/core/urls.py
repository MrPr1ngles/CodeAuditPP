from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('logout-success/', views.logout_success_view, name='logout_success'),
    path('create-session/', views.create_session_view, name='create_session'),
    path('my-sessions/', views.sessions_list_view, name='sessions_list'),
   # path('delete-session/<str:code>/', views.delete_session, name='delete_session'),
    path('session/<str:code>/', views.session_detail_view, name='session_detail'),
    path('join-session/', views.join_session_view, name='join_session'),
    path('code-editor/<str:code>/', views.code_editor_view, name='code_editor'),
    path('examiner-editor/<str:code>/', views.examiner_editor_view, name='examiner_editor'),
    path('session/<str:code>/delete/', views.delete_session, name='delete_session'),
]
