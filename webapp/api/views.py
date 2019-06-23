from braces.views import GroupRequiredMixin
from django.views.generic import View
from ordering.models import OrderRound
from pytz import UTC
from datetime import datetime
from .utils import CSVResponse, JSONResponse
from accounts.models import VokoUser


class OrdersAPIView(GroupRequiredMixin, View):
    group_required = ('IT', 'Promo')

    def get_raw_data(self):
        now = datetime.now(UTC)
        data = []
        order_rounds = OrderRound.objects.all() \
            .filter(closed_for_orders__lt=now) \
            .order_by("open_for_orders")
        for order_round in order_rounds:
            products = order_round.products.all()
            suppliers = set()
            for product in products:
                suppliers.add(product.supplier.name)
            paid_orders = order_round.orders.filter(paid=True)
            ordering_members = set()
            for order in paid_orders:
                ordering_members.add(order.user.id)
            members = VokoUser.objects \
                .filter(created__lt=order_round.open_for_orders)

            data.append({
                'open_for_orders_date': order_round.open_for_orders.date(),
                'number_of_orders': order_round.number_of_orders(),
                'number_of_ordering_members': len(ordering_members),
                'number_of_members': members.count(),
                'total_revenue': order_round.total_revenue(),
                'number_of_products': products.count(),
                'numbers_of_suppliers': len(suppliers),
                'markup_percentage': order_round.markup_percentage
            })
        return data


class OrdersJSONView(OrdersAPIView):
    def get(self, request, *args, **kwargs):
        return JSONResponse(self.get_raw_data())


class OrdersCSVView(OrdersAPIView):
    def get(self, request):
        return CSVResponse(self.get_raw_data())


class AccountsAPIView(GroupRequiredMixin, View):
    group_required = ('IT', 'Promo')

    def get_raw_data(self, include_empty_fields):
        data = []
        users = VokoUser.objects.all()
        for user in users:
            field = {
                'created_date': user.created.date(),  # rounded to day
                'is_active': user.is_active,
                'is_asleep': user.is_asleep,
            }

            email_confirmation = user.email_confirmation
            if email_confirmation.is_confirmed:
                field['confirmed_date'] = email_confirmation.modified.date()
            elif include_empty_fields:
                field['confirmed_date'] = None

            if user.is_active and user.activated is not None:
                field['activated_date'] = user.activated.date()
            elif include_empty_fields:
                field['activated_date'] = None

            paid_orders = user.orders.filter(paid=True).order_by("modified")
            first_paid_order = paid_orders.first()
            if first_paid_order:
                field['first_order_date'] = first_paid_order.modified.date()
            elif include_empty_fields:
                field['first_order_date'] = None

            data.append(field)
        return data


class AccountsJSONView(AccountsAPIView):
    def get(self, request, *args, **kwargs):
        return JSONResponse(self.get_raw_data(False))


class AccountsCSVView(AccountsAPIView):
    def get(self, request):
        return CSVResponse(self.get_raw_data(True))


class AccountsAdminAPIView(GroupRequiredMixin, View):
    group_required = ('Admin')

    def get_raw_data(self, include_empty_fields):
        data = []
        users = VokoUser.objects.all()
        for user in users:
            item = {
                'created_date': user.created.date(),  # rounded to day
            }

            # copy user fields
            user_fields = {
                "first_name",
                "last_name",
                "email",
                "can_activate",
                "is_active",
                "is_staff",
                "is_asleep"
            }
            for field in user_fields:
                item[field] = getattr(user, field, "")

            # copy user profile fields
            profile_fields = {
                "phone_number",
                "has_drivers_license"
            }
            if include_empty_fields:
                for field in profile_fields:
                    item[field] = ""
            try:
                for field in profile_fields:
                    item[field] = getattr(user.userprofile, field)
            except user._meta.model.userprofile.RelatedObjectDoesNotExist:
                pass

            # email confirmation
            email_confirmation = user.email_confirmation
            item['is_confirmed'] = email_confirmation.is_confirmed
            if email_confirmation.is_confirmed:
                item['confirmed_date'] = email_confirmation.modified.date()
            elif include_empty_fields:
                item['confirmed_date'] = None

            # activated
            if user.is_active and user.activated is not None:
                item['activated_date'] = user.activated.date()
            elif include_empty_fields:
                item['activated_date'] = None

            # first_paid_order
            paid_orders = user.orders.filter(paid=True).order_by("modified")
            first_paid_order = paid_orders.first()
            if first_paid_order:
                item['first_order_date'] = first_paid_order.modified.date()
            elif include_empty_fields:
                item['first_order_date'] = None

            # groups
            item['groups'] = ",".join(user.flat_groups())

            data.append(item)
        return data


class AccountsAdminJSONView(AccountsAdminAPIView):
    def get(self, request, *args, **kwargs):
        return JSONResponse(self.get_raw_data(False))


class AccountsAdminCSVView(AccountsAdminAPIView):
    def get(self, request):
        return CSVResponse(self.get_raw_data(True))
