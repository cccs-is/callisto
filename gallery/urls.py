from django.urls import path
from . import views, views_notebook_details

urlpatterns = [
    path('', views.index, name='index'),
    path('about/', views.about, name='about'),
    path('login/', views.login_user, name='login-user'),
    path('delete-user/', views.delete_user, name='delete-user'),
    path('shared/', views.shared, name='shared'),
    path('logout/', views.logout_user, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('notebooks/', views.notebook_index, name='notebook-index'),
    path('search/', views.search_notebooks, name='search'),
    path('likes/', views.likes, name='likes'),
    path('sources/', views.data_source_index, name='data-source-index'),
    path('nbupload/', views.nbupload, name='nbupload'),
    path('notebook_by_source/', views.notebook_by_source, name='notebook_by_source'),
    path('notebook/<notebook_id>/', views_notebook_details.notebook_details, name='notebook-details'),
    path('open-notebook/<notebook_id>/', views_notebook_details.open_notebook_hub, name='open-notebook'),
    path('edit-notebook/<notebook_id>/', views.edit_notebook, name='edit-notebook'),
    path('render-notebook/<notebook_id>/', views_notebook_details.render_notebook, name='render-notebook'),
    path('delete-notebook/<notebook_id>/', views.delete_notebook, name='delete-notebook'),
    path('upload-notebook/', views.upload_notebook, name='upload-notebook'),
    path('add-comment/<notebook_id>/', views.add_comment, name='add-comment'),
    path('like-notebook/<notebook_id>/', views_notebook_details.like_notebook, name='like-notebook')
]
