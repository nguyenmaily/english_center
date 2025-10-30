from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.core.paginator import Paginator

from .serializers import ChangePasswordSerializer
from .models import Manager, Teacher


@login_required
@require_http_methods(["GET", "POST"])
def profile_view(request):
    user = request.user
    if request.method == 'POST':
        allowed_fields = ['email', 'fullname', 'phone', 'sex', 'dob', 'urlImage']
        for field in allowed_fields:
            if field in request.POST:
                setattr(user, field, request.POST.get(field) or None)
        user.save()
        messages.success(request, 'Cập nhật hồ sơ thành công!')
        if request.headers.get('HX-Request'):
            return render(request, 'users/partials/profile_card.html', {'user': user})
        return redirect('profile')
    return render(request, 'users/profile.html', {'user': user})


@login_required
@require_http_methods(["GET", "POST"])
def change_password_view(request):
    if request.method == 'POST':
        data = {
            'old_password': request.POST.get('old_password'),
            'new_password': request.POST.get('new_password'),
            'confirm_password': request.POST.get('confirm_password'),
        }
        serializer = ChangePasswordSerializer(data=data)
        if serializer.is_valid():
            user = request.user
            if not user.check_password(serializer.validated_data['old_password']):
                return render(request, 'users/change_password.html', {'errors': {'old_password': ['Mật khẩu cũ không đúng.']}}, status=400)
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            messages.success(request, 'Đổi mật khẩu thành công. Vui lòng đăng nhập lại.')
            return redirect('login')
        return render(request, 'users/change_password.html', {'errors': serializer.errors}, status=400)
    return render(request, 'users/change_password.html')


@login_required
def user_list_view(request):
    User = get_user_model()
    queryset = User.objects.select_related('roleid').all()
    user = request.user
    # Thu hẹp giống API cơ bản cho manager (đơn giản hoá)
    if hasattr(user, 'roleid') and getattr(user.roleid, 'name', None) != 'admin':
        # Manager xem trong campus của mình + bản thân
        try:
            campus = user.manager_profile.campus
            teacher_ids = Teacher.objects.filter(campus=campus).values_list('user_account_id', flat=True)
            manager_ids = Manager.objects.filter(campus=campus).values_list('user_account_id', flat=True)
            queryset = queryset.filter(Q(id__in=teacher_ids) | Q(id__in=manager_ids) | Q(id=user.id))
        except Exception:
            queryset = queryset.filter(id=user.id)
    role = request.GET.get('role')
    if role:
        queryset = queryset.filter(roleid__name=role)

    q = request.GET.get('q')
    if q:
        queryset = queryset.filter(Q(username__icontains=q) | Q(email__icontains=q) | Q(fullname__icontains=q))

    paginator = Paginator(queryset, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    return render(request, 'users/user_list.html', {'users': page_obj.object_list, 'page_obj': page_obj})


@login_required
def user_detail_view(request, id):
    User = get_user_model()
    user_obj = User.objects.select_related('roleid').get(id=id)
    return render(request, 'users/user_detail.html', {'u': user_obj})


