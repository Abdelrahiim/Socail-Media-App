from django.urls import path 
from .views import ChatIndexView ,RoomView
urlpatterns = [
    path('',ChatIndexView.as_view(),name="chat"),
    path("room/<str:slug>",RoomView.as_view(),name = "room")
]
