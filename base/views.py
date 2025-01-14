from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib.auth import authenticate,login,logout
from django.http import HttpResponse

from .forms import RoomForm,UserForm
from .models import Room, Topic, Message


def loginPage(request):
    page = 'login'  # This identifies that it's the login page
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == "POST":
        username = request.POST.get('username').lower()
        password = request.POST.get('password')

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            messages.error(request, 'Username not found')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password')

    # Pass the 'page' variable to the template
    context = {'page': page}
    return render(request, 'base/login_register.html', context)


def logoutUser(request):
    logout(request)
    return redirect('home')


def registerPage(request):
    page = 'register'  # This identifies that it's the register page
    form = UserCreationForm(request.POST or None)

    if form.is_valid():
        user = form.save(commit=False)
        user.username = user.username.lower()
        user.save()
        login(request, user)
        return redirect('home')
    else:
        messages.error(request, 'An error occurred during registration')

    # Pass the 'page' variable to the template
    context = {'form': form, 'page': page}
    return render(request, 'base/login_register.html', context)


def home(request):
    q=request.GET.get('q') if request.GET.get('q')!=None else ''

    rooms = Room.objects.filter(Q(topic__name__contains= q) |
                                Q(name__contains= q)  |
                                Q(description__contains= q))
    topics = Topic.objects.all()[0:5]
    room_count = Room.objects.count()
    room_messages = Message.objects.all().filter(Q(room__topic__name__icontains= q) )
    context = {'rooms': rooms, 'topics': topics, 'room_count': room_count,'room_messages' : room_messages}
    return render(request, 'base/home.html',context)


def room(request,pk):
    room = Room.objects.get(id=pk)
    room_messages = room.message_set.all().order_by('-created')
    participants = room.participants.all()

    if request.method == "POST":
        message = Message.objects.create(
            user=request.user,
            room=room,
            body=request.POST['body'],
        )
        room.participants.add(request.user)
        return redirect('room',pk=room.id)

    context = {'room': room,'room_messages':room_messages,'participants': participants}
    return render(request, 'base/room.html',context)

def userProfile(request,pk):
    user = User.objects.get(id=pk)
    rooms= user.room_set.all()
    room_messages = user.message_set.all().order_by('-created')
    topics = Topic.objects.all()
    context = {'user': user, 'rooms': rooms, 'room_messages': room_messages,'topics': topics}
    return render(request, 'base/profile.html',context)

@login_required(login_url='login')
def createRoom(request):
    form = RoomForm()
    topics = Topic.objects.all()

    if request.method == 'POST':
        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name=topic_name)

        Room.objects.create(
            host=request.user,
            topic=topic,
            name=request.POST.get('name'),
            description=request.POST.get('description'),
        )
        return redirect('home')

    context = {'form':form,'topics':topics }
    return render(request, 'base/room_form.html',context)


@login_required(login_url='login')
def updateRoom(request, pk):
    room = Room.objects.get(id=pk)
    form = RoomForm(instance=room)
    topics = Topic.objects.all()

    if request.user != room.host:
        return HttpResponse('You are not authorized')

    if request.method == 'POST':
        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name=topic_name)
        room.name = request.POST.get('name')
        room.topic = topic
        room.description = request.POST.get('description')
        room.save()
        return redirect('home')
    context = {'form': form,'topics' : topics, 'room': room}
    return render(request, 'base/room_form.html',context)

@login_required(login_url='login')
def deleteRoom(request, pk):
    room = Room.objects.get(id=pk)

    if request.user != room.host:
        return HttpResponse('You are not authorized')

    if request.method == 'POST':
        room.delete()
        return redirect('home')
    return render(request, 'base/delete.html',{'obj':room})


@login_required(login_url='login')
def deleteMessage(request, pk):
    message = Message.objects.get(pk=pk)
    if request.user != message.user:
        return HttpResponse('You are not authorized')
    if request.method == 'POST':
        room_id = message.room.id
        message.delete()
        return redirect('room', pk=room_id)
    return render(request, 'base/delete.html',{'obj':message})


@login_required(login_url='login')
def updateUser(request):
    user = request.user
    form = UserForm(request.POST, instance=user)

    if request.method == 'POST':
        form.save()
        return redirect('user-profile', pk=user.id)
    return render(request, 'base/update-user.html',{'form':form})

def topicPage(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''
    topics = Topic.objects.filter(name__icontains=q)

    return render(request, 'base/topics.html',{'topics':topics})

def activityPage(request):
    room_messages = Message.objects.all()[0:5]
    return render(request, 'base/activity.html',{'room_messages':room_messages})