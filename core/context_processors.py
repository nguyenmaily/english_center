from campus.models import Campus


def campuses(request):
    """
    Context processor để truyền danh sách campus vào tất cả templates
    """
    try:
        campuses_list = list(Campus.objects.all()[:6])  # Lấy tối đa 6 cơ sở
    except Exception:
        campuses_list = []
    return {
        'campuses': campuses_list,
    }

