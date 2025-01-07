from django.shortcuts import render,redirect,get_object_or_404
from django.contrib import messages
from adminapp.models import *
from datetime import date
import urllib.request
import urllib.parse
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import random
from django.contrib.auth import logout
from django.core.mail import send_mail
import os
import random
from django.conf import settings
from userapp.models import *
from adminapp.models import *


# Create your views here.

def user_logout(request):
    logout(request)
    messages.info(request, "Logout Successfully ")
    return redirect("user_login")


# Create your views here.




EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')






def generate_otp(length=4):
    otp = "".join(random.choices("0123456789", k=length))
    return otp



def index(request):
    return render(request,"user/index.html")


def about(request):
    return render(request,"user/about.html")


def user_login(request):
    if request.method == "POST":
        aadhar = request.POST.get("aadhar", "").strip()
        password = request.POST.get("password", "").strip()

        if not aadhar or not password:
            messages.error(request, "Aadhar number and password are required.")
            return redirect("user_login")

        try:
            user = UserDetails.objects.get(aadhar_number=aadhar)

            if user.password != password:
                messages.error(request, "Incorrect password.")
                return redirect("user_login")

            if user.status == "Pending":
                request.session["user_id_after_login"] = user.pk
                messages.success(request, "Login successful!")
                return redirect("user_dashboard")

            elif user.status == "Hold":
                messages.error(request, "Your account is temporarily on hold. Please contact the admin for more details.")
                return redirect("user_login")

            else:
                messages.error(request, "Account status is not valid. Please contact support.")
                return redirect("user_login")

        except UserDetails.DoesNotExist:
            messages.error(request, "Aadhar number not registered.")
            return redirect("user_login")
        
    return render(request, "user/user-login.html")



from django.utils.datastructures import MultiValueDictKeyError


def user_profile(request):
    user_id  = request.session.get('user_id_after_login')
    print(user_id)
    user = UserDetails.objects.get(pk= user_id)
    if request.method == "POST":
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        try:
            profile = request.FILES['profile']
            user.photo = profile
        except MultiValueDictKeyError:
            profile = user.photo
        password = request.POST.get('password')
        location = request.POST.get('location')
        user.user_name = name
        user.email = email
        user.phone_number = phone
        user.password = password
        user.address = location
        user.save()
        messages.success(request , 'updated succesfully!')
        return redirect('user_profile')
    return render(request,'user/user-profile.html',{'user':user})



def admin_login(request):
    if request.method == 'POST':
        username = request.POST.get('name')
        password = request.POST.get('password')
        if username == 'admin' and password == 'admin':
            messages.success(request, 'Login Successful')
            return redirect('admin_dashboard')
        else:
            messages.error(request, 'Invalid Login Credentials')
            return redirect('admin_login')
    return render(request,"user/admin-login.html")


def contact(request):
    return render(request,"user/contact.html")


def pay_fine(request, id):
    details = FineRecord.objects.get(pk=id)
    request.session['details'] = id
    print(details.fine_amount,"hererererer")
    return render(request, "user/payment.html", {'details': details})


def user_dashboard(request):
    return render(request,"user/user-dashboard.html")


def view_and_pay(request):
    user_id = request.session.get('user_id_after_login')
    user = get_object_or_404(UserDetails, id=user_id)
    pending_fines = FineRecord.objects.filter(user=user, user_response='Pending')

    return render(request, "user/view-pay.html", {'pending_fines': pending_fines})


def payment(request):
    return render(request,"user/payment.html")



def final_payment(request):
    if request.method == 'POST':
        fine_record_id = request.POST.get('fine_record_id')
        if fine_record_id:
            fine_record = get_object_or_404(FineRecord, pk=fine_record_id)
            fine_record.user_response = 'Paid'
            fine_record.paid_at = timezone.now()
            fine_record.save()
            subject = "Fine Payment Confirmation"
            message = f"""
            Dear {fine_record.user.user_name},
            We are pleased to inform you that your fine has been successfully paid. Below are the details of the fine:
            - Fine Amount: {fine_record.fine_amount}
            - Date Issued: {fine_record.issued_at.strftime('%Y-%m-%d %H:%M:%S')}
            - Payment Date: {fine_record.paid_at.strftime('%Y-%m-%d %H:%M:%S')}
            Thank you for your prompt payment. If you have any questions or require further information, please contact us.
            Best regards,
            Smokedetection Team
            """
            from_email = settings.EMAIL_HOST_USER
            recipient_list = [fine_record.user.email]
            send_mail(subject, message, from_email, recipient_list, fail_silently=False)
            messages.success(request, 'Payment successful!')
        else:
            messages.error(request, 'Invalid request. No record ID provided.')
    else:
        messages.error(request, 'Invalid request method.')

    return redirect('view_and_pay')
    
    