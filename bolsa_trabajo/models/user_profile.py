#-*- coding: UTF-8 -*-
import hashlib
from django.db import models
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.template.loader import get_template
from BolsaTrabajo.bolsa_trabajo.utils import *
from . import Offer, OfferComment, Student, Enterprise, Tag
from BolsaTrabajo import settings
from django.core.urlresolvers import reverse

class UserProfile(models.Model):
    validated_email = models.BooleanField(default = False)
    user = models.OneToOneField(User, related_name = 'profile')
    tags = models.ManyToManyField(Tag, blank = True, null = True)
    block_public_access = models.BooleanField(default = False)   

    def __unicode__(self):  
        return 'Perfil de %s' % self.user
        
    def get_notifications(self):
        notifications = []
        if self.user.is_staff:
            return notifications    
        elif self.is_student():
            unread_offer_comment_replies = OfferComment.objects.filter(author = self.user, has_replies = True)
            for reply in unread_offer_comment_replies:
                notifications.append(['Nueva respuesta en tu comentario para %s' % reply.offer.title, reverse('bolsa_trabajo.views.offer_details', args = [reply.offer.id])])
                
            unread_enterprise_comment_replies = EnterpriseComment.objects.filter(author = self.user, has_replies = True)
            for reply in unread_enterprise_comment_replies:
                notifications.append(['Nueva respuesta en tu comentario para la empresa %s' % reply.enterprise.name, reverse('bolsa_trabajo.views.enterprise_details', args = [reply.enterprise.id])])
            
        else:
            enterprise = Enterprise.objects.get(pk = self.user.id)
            unread_offer_comments = Offer.objects.filter(enterprise = enterprise, has_unread_comments = True)
            
            for offer in unread_offer_comments:
                notifications.append(['Nuevo comentario para la oferta %s' % offer.title, reverse('bolsa_trabajo.views.offer_details', args = [offer.id])])
            
            if enterprise.has_unread_comments:
                notifications.append(['Nuevo comentario para la empresa', reverse('bolsa_trabajo.views.enterprise_details', args = [enterprise.id])])
                
        return notifications
        
    def can_reply(self, offer):
        response = False
        if self.user.is_authenticated() and self.user.is_active:
            if self.is_student() or self.user.id == offer.enterprise.id:
                response = True
                
        return response
        
    def can_reply_to_enterprise(self, enterprise):
        response = False
        if self.user.is_authenticated() and self.user.is_active:
            if self.is_student() or self.user.id == enterprise.id:
                response = True
                
        return response
        
    class Meta:
        app_label = 'bolsa_trabajo'
        
    @staticmethod
    def notify_staff_of_new_register():
        users = User.objects.filter(is_staff = True).filter(is_superuser = False)
        for user in users:
            user.profile.send_new_register_mail()
            
    def send_new_register_mail(self):
        subject = '[Bolsa Trabajo CaDCC] Nueva empresa solicita autorización'

        t = get_template('mails/new_enterprise_request.html')

        send_email(self.user, subject, t, {})
        
    def send_register_mail(self):
        self.send_confirmation_mail_from_template('mails/confirmation_mail.html')
        
    def send_change_mail_confirmation(self):
        self.send_confirmation_mail_from_template('mails/change_mail.html')    
        
    def send_confirmation_mail_from_template(self, template):
        subject = '[Bolsa Trabajo CaDCC] Confirmación de correo electrónico'
        user_digest = hashlib.sha224(settings.SECRET_KEY + self.user.username + self.user.email).hexdigest()

        t = get_template(template)
        args = {'user_digest': user_digest}

        send_email(self.user, subject, t, args)
        
    def error_list(self):
        if self.is_student():
            return ''
        elif self.is_enterprise():
            return 'Enterprise'
        else:
            raise Exception
        
    def is_student(self):
        students = Student.objects.filter(pk = self.user.id)
        if students:
            return True
        else:
            return False
            
    def is_enterprise(self):
        sek = self.user.id
        enterprises = Enterprise.objects.filter(pk = self.user.id)
        if enterprises:
            return True
        else:
            return False

def create_user_profile(sender, instance, created, **kwargs):  
    if created:
        profile, created = UserProfile.objects.get_or_create(user = instance)

post_save.connect(create_user_profile, sender = User) 
post_save.connect(create_user_profile, sender = Student) 
post_save.connect(create_user_profile, sender = Enterprise) 