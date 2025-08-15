def user_groups(request):
    if request.user.is_authenticated:
        return {
            'is_hyanah': request.user.groups.filter(name='Hyanah').exists(),
            'is_zasvarlah': request.user.groups.filter(name='Zasvarlah').exists(),
            'is_tailan': request.user.groups.filter(name='Tailan').exists(),
        }
    return {
        'is_hyanah': False,
        'is_zasvarlah': False,
        'is_tailan': False,
    }
