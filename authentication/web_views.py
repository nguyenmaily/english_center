from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.http import require_http_methods
from django.http import HttpResponse
from django.core.cache import cache
from django.core.mail import send_mail
import random

from .serializers import UserRegistrationSerializer, ForgotPasswordSerializer, ResetPasswordSerializer


@require_http_methods(["GET", "POST"])
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, 'Đăng nhập thành công!')
            next_url = request.GET.get('next') or 'home'
            if request.headers.get('HX-Request'):
                return HttpResponse(status=204, headers={'HX-Redirect': redirect(next_url).url})
            return redirect(next_url)
        context = {'error': 'Tên đăng nhập hoặc mật khẩu không đúng.', 'username': username}
        template = 'authentication/partials/login_form.html' if request.headers.get('HX-Request') else 'authentication/login.html'
        status = 400
        return render(request, template, context, status=status)
    return render(request, 'authentication/login.html')


def logout_view(request):
    logout(request)
    messages.info(request, 'Bạn đã đăng xuất.')
    if request.headers.get('HX-Request'):
        return HttpResponse(status=204, headers={'HX-Redirect': redirect('home').url})
    return redirect('home')


@require_http_methods(["GET", "POST"])
def register_view(request):
    if request.method == 'POST':
        data = {
            'username': request.POST.get('username'),
            'email': request.POST.get('email'),
            'password': request.POST.get('password'),
            'password_confirm': request.POST.get('password_confirm'),
            'fullname': request.POST.get('fullname') or '',
            'phone': request.POST.get('phone') or '',
            'sex': request.POST.get('sex') or 'other',
            'dob': request.POST.get('dob') or None,
            'role': 'student',
        }
        serializer = UserRegistrationSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            messages.success(request, 'Đăng ký thành công. Vui lòng đăng nhập!')
            return redirect('login')
        return render(request, 'authentication/register.html', {'errors': serializer.errors, 'form': data}, status=400)
    return render(request, 'authentication/register.html')


@require_http_methods(["GET", "POST"])
def forgot_password_view(request):
    if request.method == 'POST':
        data = {'email': request.POST.get('email')}
        serializer = ForgotPasswordSerializer(data=data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            otp = ''.join([str(random.randint(0,9)) for _ in range(6)])
            cache.set(f'password_reset_otp:{email}', otp, timeout=600)
            try:
                send_mail(
                    subject='Mã OTP đặt lại mật khẩu',
                    message=f'Mã OTP của bạn là: {otp}. Hết hạn trong 10 phút.',
                    from_email=None,
                    recipient_list=[email],
                    fail_silently=True
                )
            except Exception:
                pass
            messages.success(request, 'Đã gửi OTP tới email của bạn.')
            return redirect('reset-password')
        return render(request, 'authentication/forgot_password.html', {'errors': serializer.errors, 'form': data}, status=400)
    return render(request, 'authentication/forgot_password.html')


@require_http_methods(["GET", "POST"])
def reset_password_view(request):
    if request.method == 'POST':
        data = {
            'email': request.POST.get('email'),
            'otp': request.POST.get('otp'),
            'new_password': request.POST.get('new_password'),
            'confirm_password': request.POST.get('confirm_password'),
        }
        serializer = ResetPasswordSerializer(data=data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            otp = serializer.validated_data['otp']
            cache_key = f'password_reset_otp:{email}'
            cached_otp = cache.get(cache_key)
            if cached_otp != otp:
                return render(request, 'authentication/reset_password.html', {
                    'errors': {'otp': ['OTP không hợp lệ hoặc đã hết hạn.']},
                    'form': data
                }, status=400)
            # Update password
            from .models import UserAccount
            try:
                user = UserAccount.objects.get(email=email)
                user.set_password(serializer.validated_data['new_password'])
                user.save()
                cache.delete(cache_key)
                messages.success(request, 'Đặt lại mật khẩu thành công. Vui lòng đăng nhập!')
                return redirect('login')
            except UserAccount.DoesNotExist:
                return render(request, 'authentication/reset_password.html', {'errors': {'email': ['Email không tồn tại']}, 'form': data}, status=400)
        return render(request, 'authentication/reset_password.html', {'errors': serializer.errors, 'form': data}, status=400)
    return render(request, 'authentication/reset_password.html')


