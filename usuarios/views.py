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
    
from ventas.models import Pedido
from .forms import UserForm, PerfilForm
from django.shortcuts import render, redirect

@login_required           
def mi_cuenta(request):
    usuario = request.user
    perfil = usuario.perfil
    
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=usuario)
        perfil_form = PerfilForm(request.POST, instance=perfil)
        if user_form.is_valid() and perfil_form.is_valid():
            user_form.save()
            perfil_form.save()
            messages.success(request, "Tus datos han sido actualizados exitosamente.")
            return redirect('usuarios:mi_cuenta')
    else:
        user_form = UserForm(instance=usuario)
        perfil_form = PerfilForm(instance=perfil)

    # Obtenemos los pedidos del usuario
    pedidos = Pedido.objects.filter(usuario=usuario).order_by('-fecha_pedido')

    context = {
        'user_form': user_form,
        'perfil_form': perfil_form,
        'pedidos': pedidos,
    }
    return render(request, 'usuarios/mi_cuenta.html', context)