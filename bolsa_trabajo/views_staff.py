#-*- coding: UTF-8 -*-
import hashlib
from django.contrib import auth
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect
from forms import *
from models import *
from utils import *
    
def staff_login_required(f):
    def wrap(request, *args, **kwargs):
        if request.user.is_staff:
            return f(request, *args, **kwargs)
        else:
            url = reverse('bolsa_trabajo.views_account.login')
            path = request.path
            return HttpResponseRedirect(url + '?next=' + path)
            
    return wrap
    
@staff_login_required
def pending_enterprise_request(request):
    return append_account_metadata_to_response(request, 'staff/pending_enterprise_request.html', {
        'pending_requests': Enterprise.get_pending_requests()
    })
    
@staff_login_required
def pending_enterprise_request_details(request, request_id):
    try:
        enterprise = Enterprise.objects.get(pk = request_id)
        if enterprise.is_active:
            raise Exception
        return append_account_metadata_to_response(request, 'staff/pending_enterprise_request_details.html', {
        'enterprise': enterprise
    })
    except Exception, e:
        print str(e)
        raise Exception
        url = reverse('bolsa_trabajo.views_account.index')
        return HttpResponseRedirect(url)
        
@staff_login_required
def accept_pending_enterprise_request(request, request_id):
    try:
        enterprise = Enterprise.objects.get(pk = request_id)
        if enterprise.is_active:
            raise Exception
        enterprise.is_active = True
        enterprise.save()
        enterprise.notify_acceptance()
        request.flash['message'] = 'Empresa aceptada exitosamente'
        url = reverse('bolsa_trabajo.views_account.pending_enterprise_request')
    except:
        url = reverse('bolsa_trabajo.views_account.index')
    return HttpResponseRedirect(url)
    
@staff_login_required
def reject_pending_enterprise_request(request, request_id):
    try:
        enterprise = Enterprise.objects.get(pk = request_id)
        if enterprise.is_active:
            raise Exception
        enterprise.delete()
        enterprise.notify_rejection()
        request.flash['message'] = 'Solicitud rechazada exitosamente'
        url = reverse('bolsa_trabajo.views_account.pending_enterprise_request')
    except:
        url = reverse('bolsa_trabajo.views_account.index')
    return HttpResponseRedirect(url)
    
@staff_login_required
def new_enterprise(request):
    error = None
    if request.method == 'POST':
        form = EnterpriseRegisterForm(request.POST) 
        if form.is_valid():
            enterprise = Enterprise.create_from_form(form)
            enterprise.is_active = True
            try:
                enterprise.save()
                
                enterprise.profile.validated_email = True
                enterprise.profile.save()
                
                request.flash['message'] = 'Empresa creada exitosamente'
                url = reverse('bolsa_trabajo.views_account.index')
                return HttpResponseRedirect(url)
            except ValidationError, e:
                error = 'El nombre de usuario ya está tomado'
            except Exception, e:
                error = 'Error desconocido'
    else:
        form = EnterpriseRegisterForm()
    return append_user_to_response(request, 'staff/new_enterprise.html',{
        'register_form': form,
        'error': error
    })