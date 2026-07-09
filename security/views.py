from django.contrib import messages
from django.contrib.auth.models import User, Group, Permission
from django.contrib.auth.views import LoginView, PasswordResetView
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

from shared.mixins import AdminOnlyMixin
from .forms import UserUpdateForm, GroupForm, PermissionForm, UsernamePasswordResetForm


# === RECUPERAR CONTRASEÑA (por usuario, no por email) ===
class UsernamePasswordResetView(PasswordResetView):
    """
    Reemplaza el password_reset de Django: el usuario ingresa su nombre de
    usuario (no su email). Si existe una cuenta activa con ese usuario, se
    envía un correo con el enlace de restablecimiento a la dirección de
    email ya registrada. Funciona para cualquier cuenta (Cliente,
    Vendedor, Analista de Compras, Administrador), sin importar si se
    registró desde la página pública o la creó el Administrador.
    """
    form_class = UsernamePasswordResetForm


# === LOGIN POR ROL (tarjetas) ===
class RoleSelectLoginView(LoginView):
    """
    GET /accounts/login/: si ya existen roles configurados, muestra una
    tarjeta por cada uno; al elegir una tarjeta se va al login ya "anclado"
    a ese rol (security:role_login), que solo deja entrar a cuentas que
    realmente tengan ese rol (o al superusuario).

    Si todavía no se ha ejecutado `setup_roles` (no existe ningún Group),
    se comporta como un login normal y sin restricciones, para que el
    sistema nunca quede sin una forma de ingresar.
    """
    template_name = 'security/role_select.html'
    redirect_authenticated_user = True

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['roles'] = Group.objects.all().order_by('name')
        return ctx

    def post(self, request, *args, **kwargs):
        # Si ya hay roles configurados, no existe un formulario legítimo
        # que envíe credenciales a esta URL (viven en security:role_login
        # para cada tarjeta). Se ignora cualquier POST directo a esta vista.
        if Group.objects.exists():
            return redirect('login')
        return super().post(request, *args, **kwargs)


class RoleLoginView(LoginView):
    """
    Login real, anclado a un rol específico (una tarjeta de role_select).
    Si las credenciales son válidas pero la cuenta no tiene asignado ese
    rol (y no es superusuario), se rechaza el acceso aunque el usuario y
    la contraseña sean correctos.
    """
    template_name = 'security/role_login.html'
    redirect_authenticated_user = True

    def dispatch(self, request, *args, **kwargs):
        self.role = get_object_or_404(Group, pk=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['role'] = self.role
        return ctx

    def form_valid(self, form):
        user = form.get_user()
        if not (user.is_superuser or user.groups.filter(pk=self.role.pk).exists()):
            form.add_error(
                None,
                f'Esta cuenta no tiene asignado el rol "{self.role.name}". '
                f'Verifica tus credenciales o elige el rol correcto.'
            )
            return self.form_invalid(form)
        return super().form_valid(form)


# === USUARIOS (solo Administrador) ===
class UserListView(AdminOnlyMixin, ListView):
    model = User
    template_name = 'security/user_list.html'
    context_object_name = 'items'
    queryset = User.objects.prefetch_related('groups').order_by('username')


class UserUpdateView(AdminOnlyMixin, UpdateView):
    model = User
    form_class = UserUpdateForm
    template_name = 'security/user_form.html'
    success_url = reverse_lazy('security:user_list')


class UserDeleteView(AdminOnlyMixin, DeleteView):
    model = User
    template_name = 'security/confirm_delete.html'
    success_url = reverse_lazy('security:user_list')


# === ROLES / GROUP (solo Administrador) ===
class GroupListView(AdminOnlyMixin, ListView):
    model = Group
    template_name = 'security/group_list.html'
    context_object_name = 'items'
    queryset = Group.objects.prefetch_related('permissions').order_by('name')


class GroupCreateView(AdminOnlyMixin, CreateView):
    model = Group
    form_class = GroupForm
    template_name = 'security/group_form.html'
    success_url = reverse_lazy('security:group_list')


class GroupUpdateView(AdminOnlyMixin, UpdateView):
    model = Group
    form_class = GroupForm
    template_name = 'security/group_form.html'
    success_url = reverse_lazy('security:group_list')


class GroupDeleteView(AdminOnlyMixin, DeleteView):
    model = Group
    template_name = 'security/confirm_delete.html'
    success_url = reverse_lazy('security:group_list')


# === PERMISOS / PERMISSION (solo Administrador) ===
class PermissionListView(AdminOnlyMixin, ListView):
    """
    Lista de permisos + matriz de asignación por rol: cada fila es un
    permiso, cada columna un rol (Group), con un checkbox que indica si
    ese rol lo tiene. Al guardar, actualiza Group.permissions para todos
    los roles de una sola vez.
    """
    model = Permission
    template_name = 'security/permission_list.html'
    context_object_name = 'items'
    queryset = Permission.objects.select_related('content_type').order_by(
        'content_type__model', 'codename'
    )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        groups = list(Group.objects.all().order_by('name'))
        for group in groups:
            group.perm_ids = set(group.permissions.values_list('id', flat=True))
        ctx['roles'] = groups
        return ctx

    def post(self, request, *args, **kwargs):
        for group in Group.objects.all():
            perm_ids = request.POST.getlist(f'role_{group.pk}')
            group.permissions.set(perm_ids)
        messages.success(request, 'Permisos por rol actualizados correctamente.')
        return redirect('security:permission_list')


class PermissionCreateView(AdminOnlyMixin, CreateView):
    model = Permission
    form_class = PermissionForm
    template_name = 'security/permission_form.html'
    success_url = reverse_lazy('security:permission_list')


class PermissionUpdateView(AdminOnlyMixin, UpdateView):
    model = Permission
    form_class = PermissionForm
    template_name = 'security/permission_form.html'
    success_url = reverse_lazy('security:permission_list')


class PermissionDeleteView(AdminOnlyMixin, DeleteView):
    model = Permission
    template_name = 'security/confirm_delete.html'
    success_url = reverse_lazy('security:permission_list')
