from django.core.urlresolvers import reverse
from ordering.models import Product, OrderProduct
from ordering.tests.factories import ProductFactory, OrderRoundFactory, OrderProductFactory, OrderFactory, \
    ProductCategoryFactory, SupplierFactory
from vokou.testing import VokoTestCase


class TestProductsView(VokoTestCase):
    def setUp(self):
        self.round = OrderRoundFactory()
        self.url = reverse('view_products')
        self.login()
        self.order = OrderFactory(paid=False, finalized=False, user=self.user, order_round=self.round)

    def test_login_required(self):
        self.logout()
        ret = self.client.get(self.url)
        self.assertEqual(ret.status_code, 302)

    def test_product_round_override(self):
        round1 = self.round
        round2 = OrderRoundFactory()
        products1 = ProductFactory.create_batch(50, order_round=round1)
        products2 = ProductFactory.create_batch(50, order_round=round2)

        ret = self.client.get(self.url)
        self.assertItemsEqual(ret.context['object_list'], products1)

        ret = self.client.get(self.url + "?round=%d" % round2.id)
        self.assertItemsEqual(ret.context['object_list'], products2)

    def test_context_contains_current_order_round(self):
        current = self.round
        other_round = OrderRoundFactory()

        ret = self.client.get(self.url)
        self.assertEqual(ret.context['current_order_round'], current)

        ret = self.client.get(self.url + "?round=%d" % other_round.id)
        self.assertEqual(ret.context['current_order_round'], other_round)

    def test_context_contains_products_ordered_by_name(self):
        ProductFactory.create_batch(50, order_round=self.round)
        ret = self.client.get(self.url)
        self.assertItemsEqual(ret.context['view'].products(), Product.objects.all().order_by('name'))

    def test_attribute_is_added_to_products_for_which_an_orderproduct_exists(self):
        order = OrderFactory(order_round=self.round, user=self.user)
        product = ProductFactory(order_round=self.round)

        odp1 = OrderProductFactory(order=order, product=product)

        ret = self.client.get(self.url)
        self.assertEqual(ret.context['view'].products()[0].ordered_amount, odp1.amount)

    def test_context_contains_categories_alphabetically_sorted(self):
        cat1 = ProductCategoryFactory(name="Zeep")
        cat2 = ProductCategoryFactory(name="Kaas")
        cat3 = ProductCategoryFactory(name="Appels")

        ret = self.client.get(self.url)
        self.assertEqual(ret.context['view'].categories()[0], cat3)
        self.assertEqual(ret.context['view'].categories()[1], cat2)
        self.assertEqual(ret.context['view'].categories()[2], cat1)

    def test_context_contains_supplier_objects(self):
        suppliers = SupplierFactory.create_batch(10)
        ret = self.client.get(self.url)
        self.assertItemsEqual(ret.context['view'].suppliers(), suppliers)

    def test_redirect_to_payment_page_when_current_order_is_finalized(self):
        OrderFactory(order_round=self.round, user=self.user, finalized=True)
        ret = self.client.get(self.url, follow=True)
        self.assertRedirects(ret, reverse('finance.choosebank'), fetch_redirect_response=True)
        self.assertMsgInResponse(ret, "Je bent doorgestuurd naar de betaalpagina "
                                      "omdat je bestelling nog niet is betaald!")

    def test_submit_without_data(self):
        ret = self.client.post(self.url)
        self.assertFalse(OrderProduct.objects.exists())
        self.assertRedirects(ret, reverse("finish_order", args=(self.order.id,)))

    def test_submit_without_data_2(self):
        OrderProductFactory.create_batch(10, product__order_round=self.round, order__user=self.user)
        ret = self.client.post(self.url)
        self.assertEqual(len(OrderProduct.objects.all()), 10)

        self.assertRedirects(ret, reverse("finish_order", args=(self.order.id,)))

    def test_order_one_product(self):
        self.assertFalse(OrderProduct.objects.exists())

        product = ProductFactory(order_round=self.round)
        ret = self.client.post(self.url, {
            "order-product-%d" % product.id: 3
        })

        odp = OrderProduct.objects.get()
        self.assertEqual(odp.product, product)
        self.assertEqual(odp.amount, 3)
        self.assertEqual(odp.order.order_round, self.round)
        self.assertEqual(odp.total_retail_price, product.retail_price * 3)
        self.assertEqual(odp.base_price, product.base_price)
        self.assertEqual(odp.retail_price, product.retail_price)

        self.assertRedirects(ret, reverse("finish_order", args=(self.order.id,)))

    def test_delete_all_products_of_user(self):
        user_odps = OrderProductFactory.create_batch(10, product__order_round=self.round, order=self.order)
        other_odps = OrderProductFactory.create_batch(10, product__order_round=self.round, order=self.order)

        data = {}
        for odp in user_odps:
            data["order-product-%d" % odp.product.id] = 0

        ret = self.client.post(self.url, data)
        self.assertEqual(len(OrderProduct.objects.all()), 10)
        self.assertItemsEqual(OrderProduct.objects.all(), other_odps)

        self.assertRedirects(ret, reverse("finish_order", args=(self.order.id,)))

    def test_delete_some_products(self):
        user_odps = OrderProductFactory.create_batch(10, product__order_round=self.round, order=self.order)
        other_odps = OrderProductFactory.create_batch(10, product__order_round=self.round, order=self.order)

        data = {}
        for odp in user_odps[:5]:
            data["order-product-%d" % odp.product.id] = ""

        ret = self.client.post(self.url, data)
        self.assertEqual(len(OrderProduct.objects.all()), 15)
        self.assertItemsEqual(OrderProduct.objects.all(), other_odps + user_odps[5:])

        self.assertRedirects(ret, reverse("finish_order", args=(self.order.id,)))

    def test_change_amounts(self):
        user_odps = OrderProductFactory.create_batch(10, product__order_round=self.round, order=self.order,
                                                     amount=5)

        data = {}
        for odp in user_odps:
            data["order-product-%d" % odp.product.id] = "3"
        ret = self.client.post(self.url, data)

        for odp in OrderProduct.objects.all():
            self.assertEqual(odp.amount, 3)

        self.assertRedirects(ret, reverse("finish_order", args=(self.order.id,)))

    def test_other_keys_in_post_data_are_ignored(self):
        odps = OrderProductFactory.create_batch(10, product__order_round=self.round, order=self.order)
        ret = self.client.post(self.url, {"order_product_999": 12,
                                          "foo": "bar"})
        self.assertItemsEqual(OrderProduct.objects.all(), odps)
        self.assertRedirects(ret, reverse("finish_order", args=(self.order.id,)))

    def test_tamper_with_ids_1(self):
        ret = self.client.post(self.url, {"order-product-0": 1}, follow=True)
        self.assertFalse(OrderProduct.objects.exists())
        self.assertRedirects(ret, reverse("view_products"))
        self.assertMsgInResponse(ret, "Er ging iets fout bij het opslaan. "
                                      "Probeer het opnieuw of neem contact met ons op.")

    def test_tamper_with_ids_2(self):
        ret = self.client.post(self.url, {"order-product-x": 1}, follow=True)
        self.assertFalse(OrderProduct.objects.exists())
        self.assertRedirects(ret, reverse("view_products"))
        self.assertMsgInResponse(ret, "Er ging iets fout bij het opslaan. "
                                      "Probeer het opnieuw of neem contact met ons op.")

    def test_order_sold_out_product(self):
        sold_out_odp = OrderProductFactory(product__order_round=self.round, order=self.order,
                                           product__maximum_total_order=1, amount=1)
        self.order.finalized = True
        self.order.paid = True
        self.order.save()
        self.assertFalse(sold_out_odp.product.is_available)

        ret = self.client.post(self.url, {"order-product-%d" % sold_out_odp.product.id : 1}, follow=True)
        self.assertMsgInResponse(ret, "Het product '%s' van %s is uitverkocht!" %
                                 (sold_out_odp.product.name, sold_out_odp.product.supplier.name))

    def test_order_more_than_max(self):
        product = ProductFactory(order_round=self.round, maximum_total_order=1)
        self.assertTrue(product.is_available)

        ret = self.client.post(self.url, {"order-product-%d" % product.id : 2}, follow=True)
        self.assertMsgInResponse(ret,  "Van het product '%s' van %s is nog %s %s beschikbaar!" %
                                 (product.name, product.supplier.name, product.amount_available,
                                  product.unit_of_measurement.lower()))
