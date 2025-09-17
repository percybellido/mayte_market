from django.shortcuts import render
from django.shortcuts import render, get_object_or_404
from .models import Producto, Categoria
from django.urls import reverse_lazy
from django.views.generic import (
    ListView,
    CreateView,
    UpdateView,
    DeleteView,
    DetailView,
    View,
)

from .forms import ProductForm

class ProductListView(ListView):
    template_name="product/producto_lista.html"
    context_object_name='productos'
    paginate_by=10

    def get_queryset(self):
        kword=self.request.GET.get("kword", '')
        order=self.request.GET.get("order", '')
        queryset=Producto.objects.buscar_producto(kword, order)
        return queryset
    
class ProductCreateView(CreateView):
    template_name="product/form_producto.html"
    form_class=ProductForm
    success_url=reverse_lazy('producto_app:producto-lista')

    def form_invalid(self, form):
        print("Formulario no válido")
        print(form.errors)
        return super().form_invalid(form)


class ProductUpdateView(UpdateView):
    template_name="product/form_producto.html"
    model=Producto
    form_class=ProductForm
    success_url=reverse_lazy('producto_app:producto-lista')

class ProductDeleteView(DeleteView):
    template_name = "product/delete.html"
    model = Producto
    success_url = reverse_lazy('producto_app:producto-lista')

class ProductDetailView(DetailView):
    template_name = "product/detail.html"
    model = Producto

class CategoryProductListView(ListView):
    model = Producto
    template_name = "product/category_list.html"
    context_object_name = "products"  # más consistente con los templates
    paginate_by=8


    def get_queryset(self):
        category_slug = self.kwargs.get('slug')
        if category_slug:
            category = get_object_or_404(Categoria, slug=category_slug)
            return Producto.objects.filter(categoria=category)
        return Producto.objects.exclude(nombre__iexact="ajuste_inicial")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Categoria.objects.exclude(nombre__iexact="servicio")
        context['current_slug'] = self.kwargs.get('slug', '')
        return context
