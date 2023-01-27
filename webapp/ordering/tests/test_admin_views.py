from django.urls import reverse

from ordering.models import ProductStock, Product
from ordering.tests.factories import (
    ProductFactory, ProductStockFactory,
    OrderRoundFactory, SupplierFactory, ProductCategoryFactory,
    ProductUnitFactory)
from vokou.testing import VokoTestCase


class TestProductStockApiView(VokoTestCase):
    def setUp(self):
        self.login(group="Boeren")
        self.url = reverse('ordering.api.productstock')

    def test_new_stock(self):
        product = ProductFactory(order_round=None)
        self.assertFalse(ProductStock.objects.all())
        self.assertEqual(product.all_stock(), 0)

        ret = self.client.post(self.url, data={
            'amount': 10,
            'product_id': product.id,
            'type': 'added',
            'notes': "foo",
            'base_price': str(product.base_price)
        })

        self.assertEqual(ret.status_code, 201)
        prod_stock = ProductStock.objects.first()

        self.assertCountEqual(product.stock.all(),
                              (prod_stock,))

        self.assertEqual(prod_stock.product, product)
        self.assertEqual(prod_stock.type, 'added')
        self.assertEqual(prod_stock.amount, 10)
        self.assertEqual(prod_stock.notes, 'foo')
        self.assertEqual(product.all_stock(), 10)

    def test_add_stock(self):
        product = ProductFactory(order_round=None)
        ProductStockFactory(product=product, amount=5)
        self.assertEqual(product.all_stock(), 5)

        ret = self.client.post(self.url, data={
            'amount': 5,
            'product_id': product.id,
            'type': 'added',
            'notes': "foo",
            'base_price': str(product.base_price)
        })

        self.assertEqual(ret.status_code, 201)
        prod_stock = ProductStock.objects.last()

        self.assertEqual(ProductStock.objects.count(), 2)

        self.assertEqual(prod_stock.product, product)
        self.assertEqual(prod_stock.type, 'added')
        self.assertEqual(prod_stock.amount, 5)
        self.assertEqual(prod_stock.notes, 'foo')

        self.assertEqual(product.all_stock(), 10)

    def test_subtract_stock(self):
        product = ProductFactory(order_round=None)
        ProductStockFactory(product=product, amount=5)
        self.assertEqual(product.all_stock(), 5)

        ret = self.client.post(self.url, data={
            'amount': 3,
            'product_id': product.id,
            'type': 'lost',
            'notes': "foo",
            'base_price': str(product.base_price)
        })

        self.assertEqual(ret.status_code, 201)
        prod_stock = ProductStock.objects.last()

        self.assertEqual(ProductStock.objects.count(), 2)

        self.assertEqual(prod_stock.product, product)
        self.assertEqual(prod_stock.type, 'lost')
        self.assertEqual(prod_stock.amount, 3)
        self.assertEqual(prod_stock.notes, 'foo')

        self.assertEqual(product.all_stock(), 2)

    def test_add_stock_with_different_price_creates_new_product(self):
        product = ProductFactory(order_round=None, base_price=1)
        ProductStockFactory(product=product, amount=5)
        self.assertEqual(product.all_stock(), 5)

        ret = self.client.post(self.url, data={
            'amount': 7,
            'product_id': product.id,
            'type': 'added',
            'notes': "foo",
            'base_price': "1.5"  # different than '1'
        })

        self.assertEqual(ret.status_code, 201)
        prod_stock = ProductStock.objects.last()

        self.assertEqual(ProductStock.objects.count(), 2)

        new_product = Product.objects.last()

        self.assertEqual(prod_stock.product, new_product)
        self.assertEqual(prod_stock.type, 'added')
        self.assertEqual(prod_stock.amount, 7)
        self.assertEqual(prod_stock.notes, 'foo')

        self.assertEqual(product.all_stock(), 5)
        self.assertEqual(new_product.all_stock(), 7)

        # Check cloned product
        self.assertEqual(new_product.base_price, 1.5)
        self.assertEqual(new_product.name, product.name)
        self.assertEqual(new_product.unit, product.unit)
        self.assertEqual(new_product.unit_amount, product.unit_amount)
        self.assertEqual(new_product.supplier, product.supplier)
        self.assertEqual(new_product.order_round, product.order_round)
        self.assertEqual(new_product.category, product.category)
        self.assertEqual(new_product.new, product.new)
        self.assertEqual(new_product.maximum_total_order,
                         product.maximum_total_order)
        self.assertEqual(new_product.enabled, product.enabled)

    def test_nonexistent_product_id(self):
        ret = self.client.post(self.url, data={
            'amount': 10,
            'product_id': 99,
            'type': 'added',
            'notes': "foo",
            'base_price': '1'
        })

        self.assertEqual(ret.status_code, 400)

    def test_missing_parameter(self):
        product = ProductFactory(order_round=None)

        ret = self.client.post(self.url, data={
            'amount': 10,
            'product_id': product.id,
            # missing 'type'
            'notes': "foo",
            'base_price': str(product.base_price)
        })

        self.assertEqual(ret.status_code, 400)

    def test_product_not_enabled(self):
        product = ProductFactory(order_round=None, enabled=False)

        ret = self.client.post(self.url, data={
            'amount': 10,
            'product_id': product.id,
            'type': 'added',
            'notes': "foo",
            'base_price': str(product.base_price)
        })

        self.assertEqual(ret.status_code, 400)

    def test_call_with_regular_non_stock_product(self):
        product = ProductFactory(order_round=OrderRoundFactory())

        ret = self.client.post(self.url, data={
            'amount': 10,
            'product_id': product.id,
            'type': 'added',
            'notes': "foo",
            'base_price': str(product.base_price)
        })

        self.assertEqual(ret.status_code, 400)


class TestProductApiView(VokoTestCase):
    def setUp(self):
        self.login(group="Boeren")
        self.url = reverse('ordering.api.product')

    def test_create_product_with_just_required_fields(self):
        supplier = SupplierFactory()

        ret = self.client.post(self.url, data={
            'name': "foo",
            'supplier': supplier.id,
            'description': 'bar',
            'base_price': "1",
        })

        self.assertEqual(ret.status_code, 201)

        product = Product.objects.last()
        self.assertEqual(product.order_round, None)
        self.assertEqual(product.name, 'foo')
        self.assertEqual(product.supplier, supplier)
        self.assertEqual(product.description, 'bar')
        self.assertEqual(product.base_price, 1)
        self.assertEqual(product.unit, None)
        self.assertEqual(product.category, None)

        self.assertFalse(ProductStock.objects.all())

    def test_create_product_with_all_fields(self):
        supplier = SupplierFactory()
        category = ProductCategoryFactory()
        unit = ProductUnitFactory()

        ret = self.client.post(self.url, data={
            'name': "foo",
            'supplier': supplier.id,
            'description': 'bar',
            'base_price': "1",
            'category': category.id,
            'unit': unit.id
        })

        self.assertEqual(ret.status_code, 201)

        product = Product.objects.last()
        self.assertEqual(product.order_round, None)
        self.assertEqual(product.name, 'foo')
        self.assertEqual(product.supplier, supplier)
        self.assertEqual(product.description, 'bar')
        self.assertEqual(product.base_price, 1)
        self.assertEqual(product.unit, unit)
        self.assertEqual(product.category, category)

    def test_missing_fields(self):
        supplier = SupplierFactory()

        ret = self.client.post(self.url, data={
            'name': "foo",
            'supplier': supplier.id
        })

        self.assertEqual(ret.status_code, 400)

    def test_create_product_with_stock(self):
        supplier = SupplierFactory()

        ret = self.client.post(self.url, data={
            'name': "foo",
            'supplier': supplier.id,
            'description': 'bar',
            'base_price': "1",
            'stock': '13',
        })

        self.assertEqual(ret.status_code, 201)

        product = Product.objects.last()
        self.assertEqual(product.order_round, None)
        self.assertEqual(product.name, 'foo')
        self.assertEqual(product.supplier, supplier)
        self.assertEqual(product.description, 'bar')
        self.assertEqual(product.base_price, 1)
        self.assertEqual(product.unit, None)
        self.assertEqual(product.category, None)

        stock = ProductStock.objects.last()

        self.assertEqual(stock.amount, 13)
        self.assertEqual(stock.product, product)
