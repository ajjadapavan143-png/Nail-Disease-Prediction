from django.shortcuts import render, redirect
from django.contrib import messages
from users.forms import UserRegistrationForm
from users.models import UserRegistrationModel, PredictionHistory

# Create your views here.
# def AdminLoginCheck(request):
#     if request.method == 'POST':
#         usrid = request.POST['login_id']
#         pswd = request.POST['password']
#         print("User ID is = ", usrid)
#         if usrid == 'admin' and pswd == 'admin':
#             return render(request, 'admins/AdminHome.html')
#         else:
#             messages.success(request, 'Please Check Your Login Details')
#             print('Error')
#     return render(request, 'AdminLogin.html', {})


def AdminLogin(request):
    if request.method == 'POST':
        username = request.POST['login_id']
        pswd = request.POST['password']
        if username == 'admin' and pswd == 'admin':
            return redirect('AdminHome') 
        return redirect('AdminLogin')    
    return render(request, 'AdminLogin.html')

def AdminHome(request):
    return render(request, 'admins/AdminHome.html',{})

def RegisterUsersView(request):
    data = UserRegistrationModel.objects.all()
    return render(request,'admins/viewregisterusers.html',{'data':data})


def ActivaUsers(request):
    if request.method == 'GET':
        id = request.GET.get('uid')
        status = 'activated'
        print("PID = ", id, status)
        UserRegistrationModel.objects.filter(id=id).update(status=status)
        data = UserRegistrationModel.objects.all()
        return render(request,'admins/viewregisterusers.html',{'data':data})

def DeleteUser(request):
    if request.method == 'GET':
        id = request.GET.get('uid')
        UserRegistrationModel.objects.filter(id=id).delete()
        # Optional: Cascade manual deletes if needed, but standard delete removes the user model.
        data = UserRegistrationModel.objects.all()
        return render(request,'admins/viewregisterusers.html',{'data':data})


def AdminPredictionHistory(request):
    loginid = request.GET.get('loginid')
    if loginid:
        history = PredictionHistory.objects.filter(loginid=loginid).order_by('-created_at')
    else:
        history = PredictionHistory.objects.all().order_by('-created_at')
    return render(request, 'admins/admin_prediction_history.html', {'history': history})