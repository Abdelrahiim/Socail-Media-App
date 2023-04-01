from django.shortcuts import render
from django.views.generic import TemplateView ,FormView
from core.models import Profile ,FollowersCount
from django.contrib.auth.models import User
from itertools import chain
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db.models import Q
from core.views import login_url
from .models import Room
# Create your views here.
class ChatIndexView(LoginRequiredMixin,TemplateView):
    login_url = login_url
    template_name = "chat-index.html"
    def get_context_data(self,**kwargs):
        
        context = super().get_context_data(**kwargs)
        if kwargs == {}:
            kwargs['users'] = User.objects.exclude(username = self.request.user.username).order_by("date_joined")
            user = kwargs['users']
        else :
            user = kwargs['users']
        user_profile = [Profile.objects.get(user=user_object)  for user_object in user]
        paginator = Paginator(user_profile,2)
        page = self.request.GET.get('page')
        all_profiles = paginator.get_page(page)
        rooms = Room.objects.all()
        context ["following_users"] = all_profiles
        context ['rooms'] = rooms
        return context
    
    def post(self, request, *args: str, **kwargs):
        if 'search' in request.POST: 
            search = request.POST['search'].strip()
            users = User.objects.filter(Q(username__icontains= search)|Q(email__icontains = search)).order_by("date_joined")
            context = self.get_context_data(users = users)
            
        else :
            context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

# class RoomsView(LoginRequiredMixin,TemplateView):
#     login_url = login_url
#     template_name ="chatroom.html"
#     def get_context_data(self, **kwargs):
#         context= super().get_context_data(**kwargs)
#         rooms = Room.objects.all()
#         context["rooms"] = rooms
#         return context

class RoomView(TemplateView):
    login_url = login_url
    template_name = "chatroom.html"
    def get_context_data(self, **kwargs) :
        context =  super().get_context_data(**kwargs)
        room = Room.objects.get(slug=kwargs['slug'])
        context['room'] = room
        return context



        
            

        


        
        
        
    
