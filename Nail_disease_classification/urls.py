from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from . import views as mainView
from admins import views as admins
from users import views as usr

urlpatterns = [
    path('admin/', admin.site.urls),

    path("", mainView.index, name="index"),
    path("index/", mainView.index, name="index"),

    path("AdminLogin/", admins.AdminLogin, name="AdminLogin"),
    path("UserLogin/", mainView.UserLogin, name="UserLogin"),
    path("UserRegisterForm/", mainView.UserRegister, name="UserRegisterForm"),

    # Admin views
    path("AdminHome/", admins.AdminHome, name="AdminHome"),
    path("RegisterUsersView/", admins.RegisterUsersView, name="RegisterUsersView"),
    path("ActivaUsers/", admins.ActivaUsers, name="ActivaUsers"),
    path("DeleteUser/", admins.DeleteUser, name="DeleteUser"),
    path("AdminPredictionHistory/", admins.AdminPredictionHistory, name="AdminPredictionHistory"),

    # User views
    path("UserRegisterActions/", usr.UserRegisterActions, name="UserRegisterActions"),
    path("UserLoginCheck/", usr.UserLoginCheck, name="UserLoginCheck"),
    path("UserHome/", usr.UserHome, name="UserHome"),
    path("training/", usr.training, name="training"),
    path("nail_prediction_view/", usr.nail_prediction_view, name="nail_prediction_view"),
    path("UserPredictionHistory/", usr.UserPredictionHistory, name="UserPredictionHistory"),
]

# Media serve in development only
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)