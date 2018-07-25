# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from django.contrib.auth.models import User, Group
from rest_framework import viewsets
from webapp.api.serializers import UserSerializers, GroupSerializers

# Create your views here.

