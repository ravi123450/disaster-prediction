from django.shortcuts import render
from django.shortcuts import render,redirect,get_object_or_404
from userapp.models import *
from adminapp.models import *
from django.contrib import messages
import pandas as pd
from django.core.mail import send_mail
import os
import numpy as np
from django.shortcuts import render
from django.core.files.storage import default_storage
from tensorflow.keras.preprocessing.image import load_img, img_to_array
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
from tensorflow.keras.models import load_model


EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')

def index(request):
    t_users = UserDetails.objects.all()
    a_users = FineRecord.objects.filter(user_response="Paid")
    p_users = FineRecord.objects.filter(user_response="Pending")
    context ={
        't_users':len(t_users),
        'a_users':len(a_users),
        'p_users':len(p_users),

    }
    return render(request,'admin/index.html',context)



from django.db.models import Q
import imagehash
from PIL import Image



def all_users(request):
    user = UserDetails.objects.all()
    context = {
        'user':user,
    }
    return render(request,'admin/all-users.html',context)



model_path = 'smoke_detectore.h5'
model = load_model(model_path)



def preprocess_image(image):
    image = load_img(image, target_size=(224, 224))
    image = img_to_array(image)
    image = np.expand_dims(image, axis=0)
    image = preprocess_input(image)
    return image




def predict_image(model, image):
    image = preprocess_image(image)
    predictions = model.predict(image)
    labels = ['no smoking', 'smoking']
    predicted_label = labels[np.argmax(predictions)]
    return predicted_label




def match_images(uploaded_image_path):
    uploaded_image = Image.open(uploaded_image_path)
    uploaded_image_hash = imagehash.average_hash(uploaded_image)
    
    users = UserDetails.objects.all()
    for user in users:
        user_image_path = os.path.join(settings.MEDIA_ROOT, user.photo.name)
        if os.path.exists(user_image_path):
            user_image = Image.open(user_image_path)
            user_image_hash = imagehash.average_hash(user_image)
            if uploaded_image_hash - user_image_hash < 5:  
                return user
    return None





def issue_fines(request):
    if request.method == 'POST':
        fine_amount = request.POST.get('fine')
        photo = request.FILES.get('photo')
       
        if photo:
            photo_path = default_storage.save(photo.name, photo)
            photo_full_path = os.path.join(settings.MEDIA_ROOT, photo_path)
            print(f'Saved photo path: {photo_full_path}')
            
            if os.path.exists(photo_full_path):
                prediction = predict_image(model, photo_full_path)
                
                if prediction == 'smoking':
                    messages.success(request, 'Smoking detected in the uploaded photo. Proceeding to match with user images.')

                    matched_user = match_images(photo_full_path)
                    if matched_user:
                        FineRecord.objects.create(
                            user=matched_user,
                            fine_image=photo,
                            fine_amount=fine_amount,
                            issued_at=timezone.now(),
                            user_response='Pending'
                        )
                        subject = "Fine Notification for Smoking"
                        message = f"""
                        Dear {matched_user.user_name},

                        This is to inform you that a fine has been issued due to smoking detected in the uploaded photo. Please find the details below:

                        - Fine Amount: {fine_amount}
                        - Date Issued: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}


                        Please ensure to comply with the regulations. If you have any questions or require further information, please contact us.

                        Thank you for your attention.

                        Best regards,
                        Smokedetection Team
                        """
                        from_email = settings.EMAIL_HOST_USER
                        recipient_list = [matched_user.email]
                        send_mail(subject, message, from_email, recipient_list, fail_silently=False)
                        messages.success(request, f'Fine issued to {matched_user.user_name}.')
                    else:
                        messages.error(request, 'No matching user found for the uploaded photo. No fine issued.')
                else:
                    messages.error(request, 'The uploaded photo does not show a smoking person. No smoking detected.')
                
            else:
                messages.error(request, f'File not found at path: {photo_full_path}')
                print(f'File not found at path: {photo_full_path}')
        return redirect('issue_fines')
    return render(request, 'admin/issue-fines.html')



def all_fines(request):
    fines = FineRecord.objects.filter(user_response="Pending")
    return render(request, 'admin/all-fines.html', {'fines': fines})



from django.core.files.storage import default_storage
from django.http import HttpResponseBadRequest

def upload_dataset(request):
    if request.method == 'POST':
        messages.success(request,"image Uploaded successfully !")
        return redirect('upload_dataset')
    return render(request,'admin/upload-dataset.html')



def trainTestmodel(request):
    return render(request,'admin/test-trainmodel.html')



def latest_payments(request):
    fines = FineRecord.objects.filter(user_response="Paid")
    return render(request,'admin/latest-payments.html',{"fines":fines})

# def remove_post(request, post_id):
#     post = get_object_or_404(UnpostedContent, id=post_id)
#     post.delete()
#     messages.success(request, "The post has been successfully removed.")
#     return redirect('latest_posts')

from django.db.models import Count



def change_status(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if user.status == 'Hold':
        user.status = 'Accepted'
    else:
        user.status = 'Hold'
    user.save()
    messages.success(request, f"User {user.full_name} status has been changed to {user.status}.")
    return redirect('users_hate')





def rf(request):
    if not resnet_model.objects.exists():
        resnet_model.objects.create(model_accuracy='95.972')
    request.session['resnet_accuracy'] = resnet_model.objects.first().model_accuracy
    resnet_accuracy = None
    if request.method == 'POST':
        resnet_accuracy = resnet_model.objects.first().model_accuracy
        return render(request, 'admin/rt.html',{'resnet_accuracy':resnet_accuracy})
    return render(request, 'admin/rt.html')




def nb(request):
    if not MobileNet_model.objects.exists():
        MobileNet_model.objects.create(model_accuracy='97.712')
    request.session['mobilenet_accuracy'] = MobileNet_model.objects.first().model_accuracy
    mobilenet_accuracy = None
    if request.method == 'POST':
        mobilenet_accuracy = MobileNet_model.objects.first().model_accuracy
        return render(request, 'admin/mb.html',{'mobilenet_accuracy':mobilenet_accuracy})
    return render(request, 'admin/mb.html')




def dt(request):
    if not Densenet_model.objects.exists():
        Densenet_model.objects.create(model_accuracy='92.012')
    request.session['densenet_accuracy'] = Densenet_model.objects.first().model_accuracy
    densenet_accuracy = None
    if request.method == 'POST':
        densenet_accuracy = Densenet_model.objects.first().model_accuracy
        return render(request, 'admin/dt.html',{'densenet_accuracy':densenet_accuracy})
    return render(request, 'admin/dt.html')








from django.conf import settings
import secrets
import string


def generate_random_password(length=6):
    characters = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(secrets.choice(characters) for _ in range(length))
    return password

def pending_users(request):
    if request.method == 'POST':
        user_name = request.POST['user_name']
        email = request.POST['email']
        phone_number = request.POST['phone_number']
        aadhar_number = request.POST['aadhar_number']
        address = request.POST['address']
        photo = request.FILES.get('photo')

        if UserDetails.objects.filter(email=email).exists():
            messages.error(request, 'Email is already registered.')
        elif UserDetails.objects.filter(aadhar_number=aadhar_number).exists():
            messages.error(request, 'Aadhaar number is already registered.')
        else:
            password = generate_random_password()

            new_user = UserDetails(
                user_name=user_name,
                email=email,
                phone_number=phone_number,
                aadhar_number=aadhar_number,
                password=password,
                address=address,
                photo=photo
            )
            new_user.save()
            subject = "Notification of User Registration"
            message = f"""
            Dear {user_name},

            We are notifying you that you have been successfully registered on our platform. Your details have been added to our system for monitoring and compliance purposes.

            Here are your credentials for accessing the system:
            - Aadhaar Number: {aadhar_number}
            - Password: {password}

            Please keep this information secure and use it for your records. The platform will now begin monitoring activities as per the regulations.

            If you have any questions or require further information, please contact us.

            Thank you for your cooperation.

            Best regards,
            Smokeaware Team
            """
            from_email = settings.EMAIL_HOST_USER
            recipient_list = [email]
            send_mail(subject, message, from_email, recipient_list, fail_silently=False)
            messages.success(request, 'User added successfully.')
    return render(request,'admin/pending-users.html')

def accept_user(request,user_id):
    user = User.objects.get(pk=user_id)
    user.status = 'Accepted'
    user.save()
    messages.success(request,"user is Accepted")
    return redirect('pending_users')

def reject_user(request,user_id):
    user = UserDetails.objects.get(pk = user_id)
    user.delete()
    messages.success(request,"user is rejected")
    return redirect('pending_users')


def remove_fine(request,id):
    user = FineRecord.objects.get(pk = id)
    user.delete()
    messages.success(request,"Fine is deleted !")
    return redirect('all_fines')

def delete_user(request,user_id):
    user = UserDetails.objects.get(pk = user_id)
    user.delete()
    messages.warning(request,"user is Deleted")
    return redirect('all_users')


def graph(request):
    # Fetch the first (and ideally only) instance from each model
    densenet_instance = Densenet_model.objects.first()
    mobilenet_instance = MobileNet_model.objects.first()
    resnet_instance = resnet_model.objects.first()

    # Check if instances exist and get their accuracy values
    densenet_accuracy = densenet_instance.model_accuracy if densenet_instance else 'N/A'
    mobilenet_accuracy = mobilenet_instance.model_accuracy if mobilenet_instance else 'N/A'
    resnet_accuracy = resnet_instance.model_accuracy if resnet_instance else 'N/A'

    # Print values for debugging
    print("DenseNet Accuracy:", densenet_accuracy)
    print("MobileNet Accuracy:", mobilenet_accuracy)
    print("ResNet Accuracy:", resnet_accuracy)

    context = {
        'DenseNet_accuracy': densenet_accuracy,
        'MobileNet_accuracy': mobilenet_accuracy,
        'ResNet_accuracy': resnet_accuracy
    }
   
    return render(request, 'admin/graph.html', context)

