# Django imports
from django.contrib import messages, admin  
from django.contrib.auth import authenticate, login, logout, get_user_model  
from django.contrib.auth.hashers import check_password  
from django.core.exceptions import PermissionDenied, ValidationError
from django.utils.decorators import method_decorator
from django.core.validators import RegexValidator, EmailValidator, URLValidator, FileExtensionValidator, MinLengthValidator, MaxLengthValidator, MaxValueValidator, MinValueValidator
from django.core.paginator import Paginator
from django.core.mail import send_mail  
from django.conf import settings  
from django.db import models, transaction, IntegrityError
from django.utils import timezone
from django import forms  
from django.http import Http404, JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404  
from django.urls import path, include, reverse_lazy  
from django.views import View  
from django.contrib.auth.forms import PasswordChangeForm
