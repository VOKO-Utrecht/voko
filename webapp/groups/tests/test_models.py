# -*- coding: utf-8 -*-
from django.contrib.auth.models import Group
from django.test import TestCase

from groups.models import GroupExt


class GroupExtModelTest(TestCase):
    """Tests for the GroupExt model."""

    def test_str_representation(self):
        """Test string representation of GroupExt."""
        group = Group.objects.create(name="Test Group")
        group_ext = GroupExt.objects.create(group=group)

        self.assertEqual(str(group_ext), "Test Group")

    def test_one_to_one_relationship(self):
        """Test GroupExt has one-to-one relationship with Group."""
        group = Group.objects.create(name="Test Group")
        group_ext = GroupExt.objects.create(group=group, email="test@example.com")

        # Access through reverse relation
        self.assertEqual(group.groupext, group_ext)

    def test_email_default_is_empty(self):
        """Test email default is empty string."""
        group = Group.objects.create(name="Test Group")
        group_ext = GroupExt.objects.create(group=group)

        self.assertEqual(group_ext.email, "")

    def test_email_can_be_set(self):
        """Test email can be set."""
        group = Group.objects.create(name="Test Group")
        group_ext = GroupExt.objects.create(group=group, email="group@vokoutrecht.nl")

        self.assertEqual(group_ext.email, "group@vokoutrecht.nl")

    def test_email_can_be_blank(self):
        """Test email can be blank."""
        group = Group.objects.create(name="Test Group")
        group_ext = GroupExt.objects.create(group=group, email="")

        self.assertEqual(group_ext.email, "")

    def test_deleting_group_deletes_extension(self):
        """Test deleting Group cascades to GroupExt."""
        group = Group.objects.create(name="Test Group")
        GroupExt.objects.create(group=group)

        group.delete()

        self.assertEqual(GroupExt.objects.count(), 0)
