"""
This module contains common imports used across the Dental application.
"""

# Django imports

# Messages framework for displaying messages to users
from django.contrib import admin
from django.contrib import messages

# Authentication framework for handling user authentication
from django.contrib.auth import authenticate, get_user_model, login, logout

# Password hashing utilities
from django.contrib.auth.hashers import check_password

# Exception handling
from django.core.exceptions import PermissionDenied, ValidationError

# Validators for form fields
from django.core.validators import (
    EmailValidator, FileExtensionValidator, MaxLengthValidator, 
    MaxValueValidator, MinLengthValidator, MinValueValidator, 
    RegexValidator, URLValidator
)

# Paginator for paginating querysets
from django.core.paginator import Paginator

# Email utilities
from django.core.mail import send_mail

# Settings configuration
from django.conf import settings

# Database models and transaction management
from django.db import IntegrityError, models, transaction

# Utilities for working with time zones
from django.utils import timezone

# Decorators for class-based views
from django.utils.decorators import method_decorator

# Form utilities
from django import forms

# HTTP utilities for handling requests and responses
from django.http import Http404, HttpResponse, JsonResponse

# Shortcuts for common view operations
from django.shortcuts import get_object_or_404, redirect, render

# URL handling utilities
from django.urls import include, path, reverse_lazy

# Class-based views
from django.views import View

# Built-in form for changing passwords
from django.contrib.auth.forms import PasswordChangeForm

# Cache page
from django.core.cache import cache
