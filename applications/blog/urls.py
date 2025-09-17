from django.urls import path
from . import views

app_name = "blog_app"

urlpatterns = [
    path("", views.BlogListView.as_view(), name="blog"),
    path("category/<int:category_id>/", views.CategoryPostListView.as_view(), name="category"),
]