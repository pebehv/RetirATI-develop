from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.conf import settings
from .forms import PublicationForm, RegisterForm, LoginForm, RecoverPasswordForm, ProfileEditForm, ChangePasswordForm
from .models import Publication, Profile, Comment, Message, Notification, UserSettings
from django.http import JsonResponse
from random import sample
from django.db.models import Q
from django.contrib import messages

# Create your views here.

def can_view_publications(viewer_user, profile_owner):
    """
    Determina si un usuario puede ver las publicaciones de otro usuario
    basado en la configuración de privacidad del dueño del perfil.
    
    Args:
        viewer_user: Usuario que quiere ver las publicaciones (puede ser None si no está autenticado)
        profile_owner: Profile del dueño de las publicaciones
    
    Returns:
        bool: True si puede ver las publicaciones, False en caso contrario
    """
    # Si es el propio usuario, siempre puede ver sus publicaciones
    if viewer_user and viewer_user.is_authenticated and viewer_user == profile_owner.user:
        return True
    
    # Obtener configuración de privacidad del dueño del perfil
    owner_settings = UserSettings.get_user_settings(profile_owner.user)
    
    # Si las publicaciones son públicas, cualquiera puede verlas
    if owner_settings.privacy == 'publico':
        return True
    
    # Si las publicaciones son privadas, solo los amigos pueden verlas
    if owner_settings.privacy == 'privado':
        # Si el viewer no está autenticado, no puede ver
        if not viewer_user or not viewer_user.is_authenticated:
            return False
        
        # Verificar si son amigos
        return profile_owner in viewer_user.profile.friends.all()
    
    # Por defecto, no permitir acceso
    return False

def get_viewable_publications_for_feed(viewer_user):
    """
    Obtiene todas las publicaciones que un usuario puede ver en su feed,
    respetando las configuraciones de privacidad de cada autor.
    
    Args:
        viewer_user: Usuario autenticado que quiere ver el feed
    
    Returns:
        QuerySet de publicaciones que puede ver
    """
    if not viewer_user.is_authenticated:
        return Publication.objects.none()
    
    profile = viewer_user.profile
    
    # Obtener IDs de perfiles amigos, seguidos y propios
    friends_ids = profile.friends.values_list('id', flat=True)
    following_ids = profile.following.values_list('id', flat=True)
    allowed_profiles = list(friends_ids) + list(following_ids) + [profile.id]
    
    # Obtener todas las publicaciones de estos perfiles
    all_publications = Publication.objects.select_related('profile__user').filter(
        profile_id__in=allowed_profiles
    ).order_by('-created_at')
    
    # Filtrar las publicaciones basándose en la privacidad
    viewable_publications = []
    for publication in all_publications:
        if can_view_publications(viewer_user, publication.profile):
            viewable_publications.append(publication.id)
    
    # Retornar las publicaciones filtradas
    return Publication.objects.select_related('profile__user').filter(
        id__in=viewable_publications
    ).order_by('-created_at')

# Página de inicio (landing page)
def index(request):
    return render(request, 'index.html')

# Páginas de autenticación
def login_view(request):
    error = None
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        try:
            user = User.objects.get(email=email)
            user_auth = authenticate(request, username=user.username, password=password)
            if user_auth is not None:
                login(request, user_auth)
                return redirect('funATIAPP:muro')
            else:
                error = 'Credenciales incorrectas.'
        except User.DoesNotExist:
            error = 'No existe usuario con ese email.'
    return render(request, 'login.html', {'error': error})

def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            # Generar un username único basado en el email
            base_username = email.split('@')[0]
            username = base_username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )
            return redirect('funATIAPP:login')
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})

def recover_password_view(request):
    if request.method == 'POST':
        form = RecoverPasswordForm(request.POST)
        if form.is_valid():
            form.save(
                request=request,
                use_https=request.is_secure(),
                email_template_name='recoverpassword_email.html',
            )
            return render(request, 'recoverpassword.html', {'form': form, 'sent': True})
    else:
        form = RecoverPasswordForm()
    return render(request, 'recoverpassword.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('funATIAPP:index')

# Páginas principales de la aplicación
@login_required
def muro_view(request):
    if request.method == 'POST':
        form = PublicationForm(request.POST, request.FILES)
        if form.is_valid():
            publication = form.save(commit=False)
            publication.profile = request.user.profile
            publication.save()
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': True})
            return redirect('funATIAPP:muro')
    
    # Obtener publicaciones que respeten la privacidad
    publications = get_viewable_publications_for_feed(request.user)
    form = PublicationForm()
    
    return render(request, 'muro.html', {
        'form': form,
        'publications': publications
    })
""" 
@login_required
def muro_view(request):
    # Obtener publicaciones que respeten la privacidad
    publications = get_viewable_publications_for_feed(request.user)
    if request.method == 'POST':
        form = PublicationForm(request.POST, request.FILES)
        if form.is_valid():
            publication = form.save(commit=False)
            publication.profile = request.user.profile
            publication.save()
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': True})
            return redirect('funATIAPP:muro')
    else:
        form = PublicationForm()
    return render(request, 'muro.html', {'form': form, 'publications': publications})
"""

@login_required
def notifications_view(request):
    # Get all notifications for the current user
    notifications = request.user.notifications.all()[:20]  # Limit to 20 most recent
    
    # Mark notifications as read when viewed
    request.user.notifications.filter(is_read=False).update(is_read=True)
    
    return render(request, 'notifications.html', {'notifications': notifications})

@login_required
def chats_view(request):
    profile = request.user.profile
    friends = profile.friends.all()
    
    # Get search query if provided
    search_query = request.GET.get('search', '')
    if search_query:
        friends = friends.filter(
            Q(user__username__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query)
        )
    
    # Add recent messages for each friend
    friends_with_messages = []
    for friend in friends:
        # Get last message between current user and this friend
        last_message = Message.objects.filter(
            Q(sender=request.user, receiver=friend.user) |
            Q(sender=friend.user, receiver=request.user)
        ).first()
        
        friends_with_messages.append({
            'friend': friend,
            'last_message': last_message
        })
    
    return render(request, 'chats-main.html', {
        'friends_with_messages': friends_with_messages,
        'search_query': search_query,
    })

@login_required
def chat_room_view(request, friend_id):
    """View for specific chat room with a friend"""
    try:
        friend_profile = Profile.objects.get(id=friend_id)
        # Check if they are friends
        if friend_profile not in request.user.profile.friends.all():
            return redirect('funATIAPP:chats')
    except Profile.DoesNotExist:
        return redirect('funATIAPP:chats')
    
    # Get chat messages between the two users
    messages = Message.objects.filter(
        Q(sender=request.user, receiver=friend_profile.user) |
        Q(sender=friend_profile.user, receiver=request.user)
    ).order_by('timestamp')[:50]  # Last 50 messages
    
    # Mark messages from friend as read
    Message.objects.filter(
        sender=friend_profile.user,
        receiver=request.user,
        is_read=False
    ).update(is_read=True)
    
    # Generate room name for WebSocket (consistent naming)
    room_name = f"{min(request.user.id, friend_profile.user.id)}_{max(request.user.id, friend_profile.user.id)}"
    
    return render(request, 'chat-room.html', {
        'friend': friend_profile,
        'messages': messages,
        'room_name': room_name,
    })

@login_required
def get_messages_api(request, friend_id):
    """API endpoint to get messages with a specific friend"""
    
    try:
        friend_profile = Profile.objects.get(id=friend_id)
        friend_user = friend_profile.user
    except Profile.DoesNotExist:
        return JsonResponse({'error': 'Friend not found'}, status=404)
    
    # Get messages
    messages = Message.objects.filter(
        Q(sender=request.user, receiver=friend_user) |
        Q(sender=friend_user, receiver=request.user)
    ).order_by('timestamp')[:50]
    
    messages_data = [{
        'id': msg.id,
        'content': msg.content,
        'media_url': msg.media.url if msg.media else None,
        'sender_id': msg.sender.id,
        'sender_username': msg.sender.username,
        'timestamp': msg.timestamp.isoformat(),
        'is_sent': msg.sender == request.user,
    } for msg in messages]
    
    return JsonResponse({'messages': messages_data})

@login_required
def search_friends_api(request):
    """API endpoint to search friends"""
    
    search_query = request.GET.get('q', '')
    profile = request.user.profile
    
    if not search_query:
        # If no search query, return all friends with their last messages
        friends = profile.friends.all()
        friends_data = []
        for friend in friends:
            # Get last message between current user and this friend
            last_message = Message.objects.filter(
                Q(sender=request.user, receiver=friend.user) |
                Q(sender=friend.user, receiver=request.user)
            ).first()
            
            friends_data.append({
                'id': friend.id,
                'username': friend.user.username,
                'first_name': friend.user.first_name,
                'last_name': friend.user.last_name,
                'avatar_url': friend.avatar.url if friend.avatar else None,
                'last_message': {
                    'content': last_message.content[:50] + '...' if last_message and len(last_message.content) > 50 else (last_message.content if last_message else ''),
                    'timestamp': last_message.timestamp.strftime('%b %d') if last_message else '',
                    'is_unread': last_message and last_message.sender != request.user and not last_message.is_read if last_message else False
                } if last_message else None
            })
    else:
        # Filter friends by search query
        friends = profile.friends.filter(
            Q(user__username__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query)
        )
        
        friends_data = [{
            'id': friend.id,
            'username': friend.user.username,
            'first_name': friend.user.first_name,
            'last_name': friend.user.last_name,
            'avatar_url': friend.avatar.url if friend.avatar else None,
        } for friend in friends]
    
    return JsonResponse({'friends': friends_data})

@login_required
def send_message_api(request):
    """API endpoint to send a message with optional media"""
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        receiver_id = request.POST.get('receiver_id')
        content = request.POST.get('content', '')
        media_file = request.FILES.get('media')
        
        if not receiver_id:
            return JsonResponse({'error': 'Receiver ID is required'}, status=400)
            
        if not content and not media_file:
            return JsonResponse({'error': 'Message content or media is required'}, status=400)
        
        try:
            receiver_profile = Profile.objects.get(id=receiver_id)
            receiver_user = receiver_profile.user
        except Profile.DoesNotExist:
            return JsonResponse({'error': 'Receiver not found'}, status=404)
        
        # Check if they are friends
        if receiver_profile not in request.user.profile.friends.all():
            return JsonResponse({'error': 'You can only send messages to friends'}, status=403)
        
        # Create the message
        message = Message.objects.create(
            sender=request.user,
            receiver=receiver_user,
            content=content,
            media=media_file if media_file else None
        )
        
        return JsonResponse({
            'success': True,
            'message': {
                'id': message.id,
                'content': message.content,
                'media_url': message.media.url if message.media else None,
                'sender_id': message.sender.id,
                'sender_username': message.sender.username,
                'timestamp': message.timestamp.isoformat(),
                'is_sent': True,
            }
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def friends_view(request):
    profile = request.user.profile
    if request.method == 'POST':
        add_friend_id = request.POST.get('add_friend')
        follow_id = request.POST.get('follow')
        unfollow_id = request.POST.get('unfollow')
        remove_friend_id = request.POST.get('remove_friend')
        if add_friend_id:
            try:
                friend_profile = Profile.objects.get(id=add_friend_id)
                profile.friends.add(friend_profile)
                friend_profile.friends.add(profile)  # amistad mutua
            except Profile.DoesNotExist:
                pass
        if follow_id:
            try:
                follow_profile = Profile.objects.get(id=follow_id)
                profile.following.add(follow_profile)
            except Profile.DoesNotExist:
                pass
        if unfollow_id:
            try:
                unfollow_profile = Profile.objects.get(id=unfollow_id)
                profile.following.remove(unfollow_profile)
            except Profile.DoesNotExist:
                pass
        if remove_friend_id:
            try:
                friend_profile = Profile.objects.get(id=remove_friend_id)
                profile.friends.remove(friend_profile)
                friend_profile.friends.remove(profile)  # eliminar mutua
            except Profile.DoesNotExist:
                pass
        return redirect('funATIAPP:friends')
    all_profiles = Profile.objects.exclude(id=profile.id)
    friends = profile.friends.all()
    # Excluir amigos y el propio usuario de las recomendaciones
    exclude_ids = list(friends.values_list('id', flat=True)) + [profile.id]
    recommendations_qs = all_profiles.exclude(id__in=exclude_ids)
    recommendations = list(recommendations_qs)
    # Si hay menos de 15/4 usuarios, ajustar el sample
    if not friends:
        num_recommend = min(15, len(recommendations))
        recommendations = sample(recommendations, num_recommend) if num_recommend > 0 else []
        return render(request, 'friends.html', {
            'friends': [],
            'recommendations': recommendations
        })
    else:
        num_recommend = min(4, len(recommendations))
        recommendations = sample(recommendations, num_recommend) if num_recommend > 0 else []
        return render(request, 'friends.html', {
            'friends': friends,
            'recommendations': recommendations
        })

@login_required
def settings_view(request):
    user_settings = UserSettings.get_user_settings(request.user)
    
    if request.method == 'POST':
        # Procesar el formulario de configuración
        privacy = request.POST.get('privacy', user_settings.privacy)
        language = request.POST.get('language', user_settings.language)
        color_theme = request.POST.get('color', user_settings.color_theme)
        theme_mode = request.POST.get('theme', user_settings.theme_mode)
        email_notifications = request.POST.get('notifications') == 'on'
        
        # Actualizar configuraciones
        user_settings.privacy = privacy
        user_settings.language = language
        user_settings.color_theme = color_theme
        user_settings.theme_mode = theme_mode
        user_settings.email_notifications = email_notifications
        user_settings.save()
        
        messages.success(request, 'Configuración guardada exitosamente.')
        return redirect('funATIAPP:settings')
    
    return render(request, 'settings.html', {
        'user_settings': user_settings
    })

@login_required
def edit_profile_view(request):
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, request.FILES, instance=request.user.profile, user=request.user)
        if form.is_valid():
            form.save(user=request.user)
            return redirect('funATIAPP:profile')
    else:
        form = ProfileEditForm(instance=request.user.profile, user=request.user)
    
    return render(request, 'edit-perfil.html', {
        'form': form,
        'profile': request.user.profile
    })

@login_required
def publication_view(request):
    return redirect('funATIAPP:muro')
"""
@login_required
def publication_view(request):
    return render(request, 'publication.html')
"""
@login_required
def profile_detail_view(request, profile_id):
    try:
        profile = Profile.objects.get(id=profile_id)
    except Profile.DoesNotExist:
        return redirect('funATIAPP:profile')
    
    # Verificar si el usuario actual puede ver las publicaciones del perfil
    can_view = can_view_publications(request.user, profile)
    if can_view:
        publications = profile.publications.order_by('-created_at')
    else:
        publications = []
    
    # Obtener configuración de privacidad del perfil
    profile_settings = UserSettings.get_user_settings(profile.user)
    is_own_profile = request.user.is_authenticated and request.user == profile.user
    
    context = {
        'profile': profile,
        'publications': publications,
        'can_view_publications': can_view,
        'profile_privacy': profile_settings.privacy,
        'is_own_profile': is_own_profile
    }
    
    return render(request, 'perfil-main.html', context)

@login_required
def profile_view(request):
    profile = request.user.profile
    # El usuario siempre puede ver sus propias publicaciones
    publications = profile.publications.order_by('-created_at')
    
    # Obtener configuración de privacidad del perfil
    profile_settings = UserSettings.get_user_settings(profile.user)
    
    context = {
        'profile': profile,
        'publications': publications,
        'can_view_publications': True,  # Siempre puede ver sus propias publicaciones
        'profile_privacy': profile_settings.privacy,
        'is_own_profile': True
    }
    
    return render(request, 'perfil-main.html', context)

@login_required
def followers_view(request, profile_id=None):
    # Permite ver los seguidores de cualquier perfil
    profile_id = request.GET.get('profile_id') or request.resolver_match.kwargs.get('profile_id')
    if profile_id:
        try:
            profile = Profile.objects.get(id=profile_id)
        except Profile.DoesNotExist:
            profile = request.user.profile
    else:
        profile = request.user.profile
    
    # Manejar acciones POST de seguir/dejar de seguir
    if request.method == 'POST' and request.user.is_authenticated:
        follow_id = request.POST.get('follow')
        unfollow_id = request.POST.get('unfollow')
        user_profile = request.user.profile
        
        if follow_id:
            try:
                follow_profile = Profile.objects.get(id=follow_id)
                user_profile.following.add(follow_profile)
            except Profile.DoesNotExist:
                pass
        
        if unfollow_id:
            try:
                unfollow_profile = Profile.objects.get(id=unfollow_id)
                user_profile.following.remove(unfollow_profile)
            except Profile.DoesNotExist:
                pass
        
        # Redirect para evitar reenvío de formulario
        redirect_url = request.path_info
        if profile_id:
            redirect_url += f'?profile_id={profile_id}'
        return redirect(redirect_url)
    
    followers = profile.followers.all()
    return render(request, 'followers.html', {'profile': profile, 'followers': followers})

@login_required
def follows_view(request, profile_id=None):
    # Permite ver los seguidos de cualquier perfil y dejar de seguir
    profile_id = request.GET.get('profile_id') or request.resolver_match.kwargs.get('profile_id')
    if profile_id:
        try:
            profile = Profile.objects.get(id=profile_id)
        except Profile.DoesNotExist:
            profile = request.user.profile
    else:
        profile = request.user.profile

    if request.method == 'POST' and request.user.is_authenticated:
        follow_id = request.POST.get('follow')
        unfollow_id = request.POST.get('unfollow')
        user_profile = request.user.profile
        
        if follow_id:
            try:
                follow_profile = Profile.objects.get(id=follow_id)
                user_profile.following.add(follow_profile)
            except Profile.DoesNotExist:
                pass
        
        if unfollow_id:
            try:
                unfollow_profile = Profile.objects.get(id=unfollow_id)
                user_profile.following.remove(unfollow_profile)
            except Profile.DoesNotExist:
                pass
        
        # Redirect para evitar reenvío de formulario
        redirect_url = request.path_info
        if profile_id:
            redirect_url += f'?profile_id={profile_id}'
        return redirect(redirect_url)

    following = profile.following.all()
    return render(request, 'follows.html', {'profile': profile, 'following': following})

# Componentes auxiliares
@login_required
def menu_main_view(request):
    context = {
        'user': request.user,
        'profile': request.user.profile
    }
    return render(request, 'menu-main.html', context)

@login_required
def container_view(request):
    # Obtener publicaciones que respeten la privacidad
    publications = get_viewable_publications_for_feed(request.user)
    return render(request, 'container.html', {'publications': publications})

@login_required
def publication_detail_view(request, id):
    publication = Publication.objects.select_related('profile__user').get(id=id)
    if request.method == 'POST':
        content = request.POST.get('content')
        parent_id = request.POST.get('parent')
        parent = Comment.objects.filter(id=parent_id).first() if parent_id else None
        if content:
            Comment.objects.create(
                publication=publication,
                user=request.user,
                content=content,
                parent=parent
            )
            return redirect('funATIAPP:publication_detail', id=id)
    comments = publication.comments.select_related('user').order_by('created_at')
    return render(request, 'publication.html', {
        'publication': publication,
        'comments': comments
    })

@login_required
def change_password_view(request):
    """View para cambiar la contraseña del usuario mediante AJAX"""
    if request.method == 'POST':
        form = ChangePasswordForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            # Re-autenticar al usuario después de cambiar la contraseña
            from django.contrib.auth import update_session_auth_hash
            update_session_auth_hash(request, request.user)
            
            return JsonResponse({
                'success': True,
                'message': 'Contraseña cambiada exitosamente.'
            })
        else:
            # Devolver errores de validación
            errors = {}
            for field, error_list in form.errors.items():
                errors[field] = error_list[0]  # Tomar solo el primer error por campo
            
            return JsonResponse({
                'success': False,
                'errors': errors
            })
    
    return JsonResponse({'success': False, 'message': 'Método no permitido.'})

@login_required
def test_chat(request, room_name):
    """Vista de prueba para WebSocket del chat"""
    return render(request, 'test_chat.html', {
        'room_name': room_name,
        'user': request.user
    })
