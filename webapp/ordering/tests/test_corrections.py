from decimal import Decimal
from ordering.models import OrderProductCorrection
from ordering.tests.factories import OrderProductFactory
from vokou.testing import VokoTestCase


class TestOrderProductCorrections(VokoTestCase):
    def setUp(self):
        pass

    def test_creating_a_correction(self):
        order_product = OrderProductFactory.create()
        OrderProductCorrection.objects.create(order_product=order_product,
                                              supplied_amount=0)

    def test_that_creating_a_correction_creates_sufficient_credit_1(self):
        order_product = OrderProductFactory.create(amount=10,
                                                   product__base_price=Decimal(1),
                                                   product__order_round__markup_percentage=Decimal(7))

        opc = OrderProductCorrection.objects.create(order_product=order_product,
                                                    supplied_amount=Decimal(5))

        self.assertEqual(opc.credit.amount, Decimal(5 * 1.07).quantize(Decimal('.01')))

    def test_that_creating_a_correction_creates_sufficient_credit_2(self):
        order_product = OrderProductFactory.create(amount=10,
                                                   product__base_price=Decimal(1),
                                                   product__order_round__markup_percentage=Decimal(7))

        opc = OrderProductCorrection.objects.create(order_product=order_product,
                                                    supplied_amount=Decimal(7))

        self.assertEqual(opc.credit.amount, Decimal(3 * 1.07).quantize(Decimal('.01')))

    def test_that_creating_a_correction_creates_sufficient_credit_3(self):
        order_product = OrderProductFactory.create(amount=10,
                                                   product__base_price=Decimal(1),
                                                   product__order_round__markup_percentage=Decimal(7))

        opc = OrderProductCorrection.objects.create(order_product=order_product,
                                                    supplied_amount=Decimal(0))

        self.assertEqual(opc.credit.amount, Decimal(10 * 1.07).quantize(Decimal('.01')))

    def test_that_saving_order_correction_does_not_alter_the_credit(self):
        order_product = OrderProductFactory.create(amount=10,
                                                   product__base_price=Decimal(1),
                                                   product__order_round__markup_percentage=Decimal(7))

        opc = OrderProductCorrection.objects.create(order_product=order_product,
                                                    supplied_amount=Decimal(0))

        self.assertEqual(opc.credit.amount, Decimal(10 * 1.07).quantize(Decimal('.01')))

        opc.supplied_amount = 10
        opc.save()

        opc = OrderProductCorrection.objects.all().get()
        self.assertEqual(opc.credit.amount, Decimal(10 * 1.07).quantize(Decimal('.01')))
