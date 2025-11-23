from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.contrib import messages 
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
class RegistroView(CreateView):
    form_class = UserCreationForm
    template_name = 'usuarios/registro.html'
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        response = super().form_valid(form)
        grupo_clientes, _ = Group.objects.get_or_create(name='Clientes')
        self.object.groups.add(grupo_clientes)
        messages.success(self.request, "✅ Usuario creado correctamente. Ya podés iniciar sesión.")
        return response
    
@login_required           
def perfil_usuario(request):
    return render(request, 'auth/perfil.html', {'usuario': request.user})          