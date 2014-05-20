from django.contrib.auth import views as auth_views
from django.conf import settings


def login_user(request, template_name='registration/login.html', extra_context=None): 
    response = auth_views.login(request, template_name) 
    if request.POST.has_key('remember_me'):   
        request.session.set_expiry(settings.SESSION_REMEMBER_DAYS * 24 * 3600) 
    return response




def get_guests_emails(guests_text):
    guest_emails = []
    if guests_text:
        for line in guests_text.splitlines():
            if '[' in line:
                from_idx = line.find('[')
                to_idx = line.find(']', from_idx + 1)
                try:
                    guest_emails.append(line[from_idx+1:to_idx])
                except:
                    pass
    return guest_emails
