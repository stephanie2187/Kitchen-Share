from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Message
from .forms import MessageForm
from django.http import JsonResponse

@login_required
def inbox(request):
    """ Display received messages for the logged-in user """
    messages = Message.objects.filter(receiver=request.user).order_by('-timestamp')
    return render(request, 'messaging/inbox.html', {'messages': messages})

@login_required
def sent_messages(request):
    """ Display sent messages for the logged-in user """
    messages = Message.objects.filter(sender=request.user).order_by('-timestamp')
    return render(request, 'messaging/sent.html', {'messages': messages})

@login_required
def send_message(request):
    """ Allow a user to send a message """
    if request.method == "POST":
        form = MessageForm(request.POST, sender=request.user)
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = request.user
            message.save()
            return redirect('inbox')
    else:
        form = MessageForm(sender=request.user)
    return render(request, 'messaging/send.html', {'form': form})

@login_required
def read_message(request, message_id):
    """ Mark a message as read """
    message = get_object_or_404(Message, id=message_id, receiver=request.user)
    message.read = True
    message.save()
    return render(request, 'messaging/read.html', {'message': message})

@login_required
def unread_message_count_api(request):
    if request.user:
        count = Message.objects.filter(receiver=request.user, read=False).count()
        return JsonResponse({'unread_count': count})
    return JsonResponse({'unread_count': 0})