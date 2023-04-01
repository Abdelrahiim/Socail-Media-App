from django.views.generic import TemplateView, View, ListView, FormView ,DeleteView 
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .models import Profile, Post, LikePost, FollowersCount ,Comment
from django.contrib.auth.mixins import UserPassesTestMixin
from braces.views import LoginRequiredMixin, SuperuserRequiredMixin
from itertools import chain
from django.http import JsonResponse 
from chat.models import Room
from numba.experimental import jitclass


# Create your views here.


login_url = 'signin'

# ---------------------------------------------------------------

class Index(LoginRequiredMixin, TemplateView):
    template_name = 'index.html'
    login_url = login_url

    # ------------------------------
    def get_context_data(self, **kwargs: any) -> dict[str, any]:
        user_object = User.objects.get(username=self.request.user.username)
        user_profile = Profile.objects.get(user=user_object)
        gg_users = Profile.objects.all()
        

        
        user_following = FollowersCount.objects.filter(follower = self.request.user.username)
        user_following_list = [users.user for users in user_following ]
        if user_following_list != []:

            feed = [(Post.objects.filter(user= usernames) | Post.objects.filter(user = self.request.user.username)).order_by('-created_at') for usernames in user_following_list]

        else:
            feed = [Post.objects.filter(user = self.request.user.username).order_by('-created_at')]

        un_followers:list = []
        userfollowers:int = 0
        
        for profile in gg_users:
            if profile.user.username not in user_following_list:
                if profile != user_profile:
                   un_followers.append(profile)
                   userfollowers = len(FollowersCount.objects.filter(user = profile.user.username))
                
                    

        
        feed_list = list(chain(*feed))
        
        
        comment_list = [Comment.objects.filter(post = post) for post in feed_list]
        comment_list = list(chain(*comment_list))


        context = {
            'user_profile':user_profile,
            "posts" : feed_list ,
            'gg_users':gg_users,
            'userfollowers' : userfollowers,
            'un_followers' : un_followers,
            'comments':comment_list
        }
        return context
    


# ---------------------------------------------------------------

class SignUp(View):
    template_name = "signup.html"
    # ------------------------------
    def post(self, request, *args, **kwargs):
        user_name = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        password2 = request.POST['password2']
        # -------------
        if password == password2:  # Check if the 2 Password are equal
            # ----------
            # check if The email exist in the database
            if User.objects.filter(email=email).exists():
                # Retrun a massage That The Email is Take
                messages.info(request, "email is Taken By another User")
                return redirect('signup')  # redirect again for the sign page
            # ----------
            # check if the user name is Taken
            elif User.objects.filter(username=user_name).exists():
                messages.info(
                    request, f"User_name '{user_name}' is already Taken By Another User")
                return redirect('signup')
            # ----------
            else:
                # create a new user with the
                user = User.objects.create_user(
                    username=user_name,
                    email=email,
                    password=password
                )
                #  save the User To the database in the auth user table
                user.save()
                
                #  log user in and redirect to setting page
                # authenticate The user
                user_login = authenticate(
                    username=user_name, password=password)
                login(request, user_login)

                # create a Profile object for the new user
                user_model = User.objects.get(username=user_name)
                new_profile = Profile.objects.create(
                    user=user_model, id_user=user_model.id,
                )
                new_profile.save()  # saving The profile to the profile model
                new_room = Room.objects.create(name = user_name.capitalize() , slug = user_name.lower())
                new_room.save()
                # redirect to the setting to Continue
                return redirect('settings')

        # -------------
        else:
            messages.info(request, "Password not Matching")
            return redirect('signup')
    # ------------------------------

    def get(self, request, *args, **kwargs):
        #  Render The Sign in Template
        return render(request=request, template_name=self.template_name)

# ---------------------------------------------------------------


class SignIn(View):
    template_name = "signin.html"
    # ------------------------------

    def post(self, request, *args, **kwargs):
        user_name = request.POST['username']
        password = request.POST['password']
        # authenticate the user
        user = authenticate(username=user_name, password=password)
        if user is not None:  # check if the user exists
            if user.is_active:  # check if the user is active
                login(request, user)
                return redirect('index')  # redirect to the main page
        else:
            messages.info(request, "Credentails Invalid")
            return redirect('signin')

    # ------------------------------
    def get(self, request, *args, **kwargs):
        return render(request=request, template_name=self.template_name)


# ---------------------------------------------------------------
class LogOut(LoginRequiredMixin, View):
    login_url = 'signin'
    # ------------------------------

    def get(self, request, *args, **kwargs):
        logout(request=request)
        return redirect("signin")

# ---------------------------------------------------------------


class Settings(LoginRequiredMixin, FormView):

    login_url = login_url
    template_name = 'setting.html'
    # ------------------------------

    def get(self, request, *args, **kwargs):
        user_profile = Profile.objects.get(user=request.user)
        return render(request, self.template_name, {'user_profile': user_profile})
    # ------------------------------

    def post(self, request, *args, **kwargs):
        user = request.user
        user_profile = Profile.objects.get(user=user)
        if request.FILES.get('image') == None:
            image = user_profile.profileimg
        else:
            image = request.FILES.get('image')

        first_name = request.POST['firstname']
        last_name = request.POST['lastname']
        bio = request.POST['bio']
        location = request.POST['location']
        email = request.POST['email']


        user.first_name = first_name
        user.last_name = last_name
        user.email = email


        user.save()
        user_profile.bio = bio
        user_profile.location = location
        user_profile.profileimg = image
        user_profile.save()

        return redirect('settings')

# ---------------------------------------------------------------


class ResetPassword(LoginRequiredMixin, FormView):
    login_url = login_url
    template_name = 'resetpassword.html'
    # ------------------------------

    def post(self, request, *args, **kwargs):
        user = request.user # get the user 

        old_password = request.POST['oldpassword'] #  get the old password
        new_password = request.POST['password']  #  get the new password
        new_password1 = request.POST['password1'] #  confirm the new password

        if (old_password == "" or None) or (new_password == "" or None):
            messages.info(request, "Required Field")
            return redirect('reset-password')
        
        # check if the old password is right
        if user.check_password(old_password): 
            # check if the new password match the confirm password

            if new_password == new_password1:
                user.set_password(new_password)
                user.save()
                return redirect('settings')
            else:
                messages.info(request, "Password not Matching")
                return redirect('reset-password')

        else:
            messages.info(request, "PLease Write The Old Password")
            return redirect('reset-password')

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)

# ---------------------------------------------------------------


class Upload(LoginRequiredMixin, View):
    login_url = "signin"
    # ------------------------------

    def post(self, request, *args, **kwargs):
        user = request.user.username
        image = request.FILES.get("upload_image")
        caption = request.POST["caption"]

        new_post = Post.objects.create(
            user=user,
            image=image,
            caption=caption
        )
        new_post.save()
        return redirect('index')
    # ------------------------------

    def get(self, request, *args, **kwargs):
        return redirect('index')

# ---------------------------------------------------------------


class LikePostView(LoginRequiredMixin, View):
    login_url = 'signin'
    # ------------------------------

    def get(self, request, *args, **kwargs):
        username = request.user.username
        post_id = request.GET.get("post_id")

        post = Post.objects.get(id=post_id)
        like_filter = LikePost.objects.filter(
            post_id=post_id, username=username).first()

        if like_filter == None:
            new_like = LikePost.objects.create(
                post_id=post_id, username=username)
            new_like.save()
            post.no_of_likes += 1
            post.save()
            return redirect('index')
        else:
            like_filter.delete()
            post.no_of_likes -= 1
            post.save()
            return redirect('index')

# ---------------------------------------------------------------


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'profile.html'
    # ------------------------------

    def get_context_data(self, **kwargs):
        follower = self.request.user.username
        user = self.kwargs['pk']
        user_object = User.objects.get(username=self.kwargs['pk'])
        user_profile = Profile.objects.get(user=user_object)
        user_posts = Post.objects.filter(
            user=self.kwargs['pk']).order_by("-created_at")
        user_posts_lenght = len(user_posts)

        userfollowers = len(
            FollowersCount.objects.filter(user=self.kwargs['pk']))
        userfollowing = len(FollowersCount.objects.filter(
            follower=self.kwargs['pk']))
        
        if FollowersCount.objects.filter(follower=follower, user=user).first():
            butten_text = "UnFollow"
        else:
            butten_text = "Follow"

        context = {
            "user_objects": user_object,
            'user_profile': user_profile,
            'user_posts': user_posts,
            'user_posts_length': user_posts_lenght,
            "button_text": butten_text,
            "followers":userfollowers,
            "following":userfollowing
        }
        return context

# ---------------------------------------------------------------


class Follow(LoginRequiredMixin, FormView):
    login_url = login_url
    # ------------------------------
    def post(self, request, *args, **kwargs):
        follower = request.user.username  #  get the currrent login user username
        user = request.POST['user'] # get the porfile user username
        direct = '/profile/'+user
        # check if the user already follow this user then unfollow 
        if FollowersCount.objects.filter(follower=follower, user=user).first():
            delete_follower = FollowersCount.objects.get(
                follower=follower, user=user)
            delete_follower.delete()
            return user
        #  if not follow
        else:
            new_follower = FollowersCount.objects.create(
                follower=follower, user=user)
            new_follower.save()
            return user
            
    
class FollowFromProfile(Follow):
    def post(self, request, *args, **kwargs):
        user = super().post(request, *args, **kwargs) 
        return redirect('/profile/'+user)

class FollowFromHome(Follow):
    def post(self, request, *args, **kwargs):
        user = super().post(request, *args, **kwargs) 
        return redirect('index')

# ---------------------------------------------------------------
class DeletePost(LoginRequiredMixin,View):
    login_url = login_url
    
    # ------------------------------
    def get(self, request, *args, **kwargs):
        post_id =  request.GET.get("post_id") # get the Post id throw the url
        username = request.user.username # get the username of the cuurent user

        post= Post.objects.get(id=post_id) #  get the Post of  the post id from the database
        # check if the user is the owner of the post
        if username == post.user:
            post.delete() # delete the post from the database
            return redirect('index')
        # if not return to the home page
        else:
            messages.info(request,"Not authorized")
            return redirect("index")
        
    
# ---------------------------------------------------------------
class SearchView(LoginRequiredMixin,FormView):
    login_url = login_url
    template_name = 'search.html'

    # ------------------------------
    def post(self, request, *args, **kwargs):

        user_object = User.objects.get(username=request.user.username) # get The user
        user_profile = Profile.objects.get(user=user_object) # get the user porfile
        user_name  = request.POST['sruser']  #  get the search user name 
        
        # check if there is a data passed from the user
        if user_name == "" :
            return render(request,self.template_name ,{"user_profile":user_profile,"username_profile_list":[] , 'srfor':user_name})
        else :
            username_object = User.objects.filter(username__icontains = user_name) # search the database for user that with user name
            username_profile = [user.id for user in username_object ] # get a list of id of all the users the match the username search
            username_profile_list = [Profile.objects.filter(id_user = id) for id in username_profile ] # return a Profile of all the matching ids
            username_profile_list  = list(chain(*username_profile_list))
            return render(request,self.template_name, context= {"user_profile":user_profile,'username_profile_list': username_profile_list,"srfor":user_name})
            
# ---------------------------------------------------------------
class CommentView(LoginRequiredMixin,FormView):
    login_url = login_url

    # ------------------------------
    def post(self, request, *args, **kwargs):
        post_id = request.POST['post-id']
        post = Post.objects.get(id = post_id)
        profile = Profile.objects.get(user=request.user)
        text = request.POST['comment'] 
        if text == "" or None :
            return 
        else:
            new_comment = Comment.objects.create(
                post = post,
                author = profile,
                text = text
            )
            new_comment.save()
            return redirect('index')
            

        

        
        
        
        


# ---------------------------------------------------------------
class UserListView(LoginRequiredMixin, SuperuserRequiredMixin, ListView):
    model = Profile
    template_name = login_url
    
    
    # ------------------------------
    # get all the user 
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['users'] = Profile.objects.all()
        return context
