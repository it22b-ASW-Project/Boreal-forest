from allauth.socialaccount.models import SocialAccount
from django.dispatch import receiver
from allauth.socialaccount.signals import social_account_added
from rest_framework.authtoken.models import Token
from allauth.account.signals import user_logged_in


@receiver(user_logged_in)
def create_auth_token(sender, request, sociallogin, **kwargs):
    print("Señal socialaccount_logged_in activada")  # Si llega aquí, la señal está funcionando
    user = sociallogin.user
    token, created = Token.objects.get_or_create(user=user)
    print(f"API Key generada para {user.username}: {token.key}")