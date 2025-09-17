from django.views.generic import ListView
from django.shortcuts import get_object_or_404
from .models import Post, Category

# ✅ Listado general de posts con paginación
class BlogListView(ListView):
    model = Post
    template_name = "blog/blog.html"
    context_object_name = "posts"
    paginate_by = 3  # número de posts por página
    ordering = ["-created"]  # opcional: ordenar por fecha descendente


# ✅ Listado de posts por categoría con paginación
class CategoryPostListView(ListView):
    model = Post
    template_name = "blog/category.html"
    context_object_name = "posts"
    paginate_by = 3

    def get_queryset(self):
        category_id = self.kwargs.get("category_id")
        self.category = get_object_or_404(Category, id=category_id)
        return Post.objects.filter(category=self.category).order_by("-created")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["category"] = self.category
        return context
