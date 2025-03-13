"""
This module contains common imports used across the Dental application.
"""

# Django imports

# Messages framework for displaying messages to users
from django.contrib import messages, admin  

# Authentication framework for handling user authentication
from django.contrib.auth import authenticate, login, logout, get_user_model  

# Password hashing utilities
from django.contrib.auth.hashers import check_password  

# Exception handling
from django.core.exceptions import PermissionDenied, ValidationError

# Decorators for class-based views
from django.utils.decorators import method_decorator

# Validators for form fields
from django.core.validators import (
    RegexValidator, EmailValidator, URLValidator, 
    FileExtensionValidator, MinLengthValidator, 
    MaxLengthValidator, MaxValueValidator, MinValueValidator
)

# Paginator for paginating querysets
from django.core.paginator import Paginator

# Email utilities
from django.core.mail import send_mail  

# Settings configuration
from django.conf import settings  

# Database models and transaction management
from django.db import models, transaction, IntegrityError

# Utilities for working with time zones
from django.utils import timezone

# Form utilities
from django import forms  

# HTTP utilities for handling requests and responses
from django.http import Http404, JsonResponse, HttpResponse

# Shortcuts for common view operations
from django.shortcuts import render, redirect, get_object_or_404  

# URL handling utilities
from django.urls import path, include, reverse_lazy  

# Class-based views
from django.views import View  

# Built-in form for changing passwords
from django.contrib.auth.forms import PasswordChangeForm
