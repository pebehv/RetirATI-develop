# signals.py
from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Profile, Notification, Comment
from .utils import send_notification_email

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(m2m_changed, sender=Profile.following.through)
def create_follow_notification(sender, instance, action, pk_set, **kwargs):
    """Create notification when someone follows a user"""
    if action == 'post_add':
        for profile_id in pk_set:
            followed_profile = Profile.objects.get(pk=profile_id)
            # Don't create notification if user follows themselves
            if instance.user != followed_profile.user:
                notification = Notification.objects.create(
                    recipient=followed_profile.user,
                    sender=instance.user,
                    notification_type='follow',
                    message=f'{instance.user.username} te está siguiendo'
                )
                # Enviar correo de notificación
                send_notification_email(notification)

@receiver(m2m_changed, sender=Profile.friends.through)
def create_friend_notification(sender, instance, action, pk_set, **kwargs):
    """Create notification when someone becomes friends with a user"""
    if action == 'post_add':
        for profile_id in pk_set:
            friend_profile = Profile.objects.get(pk=profile_id)
            # Don't create notification if user adds themselves (shouldn't happen but just in case)
            if instance.user != friend_profile.user:
                # Only create one notification per friendship (avoid duplicates)
                if not Notification.objects.filter(
                    recipient=friend_profile.user,
                    sender=instance.user,
                    notification_type='friend'
                ).exists():
                    notification = Notification.objects.create(
                        recipient=friend_profile.user,
                        sender=instance.user,
                        notification_type='friend',
                        message=f'{instance.user.username} es ahora tu amigo'
                    )
                    # Enviar correo de notificación
                    send_notification_email(notification)

@receiver(post_save, sender=Comment)
def create_comment_notification(sender, instance, created, **kwargs):
    """Create notification when someone comments on a user's publication"""
    if created:
        publication_owner = instance.publication.profile.user
        # Don't create notification if user comments on their own publication
        if instance.user != publication_owner:
            notification = Notification.objects.create(
                recipient=publication_owner,
                sender=instance.user,
                notification_type='comment',
                publication=instance.publication,
                comment=instance,
                message=f'{instance.user.username} respondió a tu publicación: "{instance.content[:50]}{"..." if len(instance.content) > 50 else ""}"'
            )
            # Enviar correo de notificación
            send_notification_email(notification)
