from django.views.generic import ListView, CreateView, UpdateView, DeleteView,DetailView
from django.urls import reverse_lazy
from .models import Categoria
from .forms import CategoriaForm
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

class CategoriaListView(ListView):
    model = Categoria
    template_name = 'categorias/categoria_list.html'
    context_object_name = 'categorias'
    paginate_by = 5

class CategoriaCreateView(CreateView):
    model = Categoria
    form_class = CategoriaForm
    template_name = 'categorias/categoria_form.html'
    success_url = reverse_lazy('categorias:categoria_list')

class CategoriaUpdateView(UpdateView):
    model = Categoria
    form_class = CategoriaForm
    template_name = 'categorias/categoria_form.html'
    success_url = reverse_lazy('categorias:categoria_list')

class CategoriaDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Categoria
    template_name = 'categorias/categoria_confirm_delete.html'
    success_url = reverse_lazy('categorias:categoria_list')

    def test_func(self):
        # Solo staff puede eliminar categorías
        return self.request.user.is_staff

class CategoriaDetailView(DetailView):
    model = Categoria
    template_name = 'categorias/categoria_detail.html'
    context_object_name = 'categoria'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Agregamos los productos asociados a la categoría
        context['productos'] = self.object.productos.all()
        return context