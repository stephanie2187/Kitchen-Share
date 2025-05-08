from .models import Message
from django.contrib.auth.decorators import login_required

def unread_message_count(request):
    if request.user.is_authenticated:
        count = Message.objects.filter(receiver=request.user, read=False).count()
    else:
        count = 0
    return {'unread_message_count': count}
