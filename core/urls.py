from django.urls import path
from . import views
urlpatterns = [
    path('',views.Index.as_view(),name='index'),
    path('signup/',views.SignUp.as_view(),name = "signup"),
    path("signin/",views.SignIn.as_view(),name = "signin"),
    path('logout/',views.LogOut.as_view(),name='logout'),
    path('settings/' , views.Settings.as_view(),name = "settings"),
    path('reset-password/',views.ResetPassword.as_view(),name = 'reset-password'),
    path("upload/",views.Upload.as_view(),name = "upload"),
    path("like-post",views.LikePostView.as_view(),name ="like-post"),
    path('profile/<str:pk>/',views.ProfileView.as_view(),name="profile"),
    path('follow/',views.FollowFromProfile.as_view(),name = 'follow'),
    path('follow-home/',views.FollowFromHome.as_view(),name = 'follow-home'),
    path('delete/',views.DeletePost.as_view(),name = 'delete'),
    path('search/',views.SearchView.as_view(),name = "search"),
    path('comment/',views.CommentView.as_view(),name = 'comment'),



    path('user-list/',views.UserListView.as_view()),
]