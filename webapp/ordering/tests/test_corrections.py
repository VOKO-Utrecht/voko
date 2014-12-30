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
                                              supplied_percentage=0)

    def test_that_creating_a_correction_creates_sufficient_credit_1(self):
        order_product = OrderProductFactory.create(amount=10,
                                                   product__base_price=Decimal(1),
                                                   product__order_round__markup_percentage=Decimal(7))

        opc = OrderProductCorrection.objects.create(order_product=order_product,
                                                    supplied_percentage=50)

        self.assertEqual(opc.credit.amount, Decimal(5 * 1.07).quantize(Decimal('.01')))

    def test_that_creating_a_correction_creates_sufficient_credit_2(self):
        order_product = OrderProductFactory.create(amount=10,
                                                   product__base_price=Decimal(1),
                                                   product__order_round__markup_percentage=Decimal(7))

        opc = OrderProductCorrection.objects.create(order_product=order_product,
                                                    supplied_percentage=70)

        self.assertEqual(opc.credit.amount, Decimal(3 * 1.07).quantize(Decimal('.01')))

    def test_that_creating_a_correction_creates_sufficient_credit_3(self):
        order_product = OrderProductFactory.create(amount=10,
                                                   product__base_price=Decimal(1),
                                                   product__order_round__markup_percentage=Decimal(7))

        opc = OrderProductCorrection.objects.create(order_product=order_product,
                                                    supplied_percentage=0)

        self.assertEqual(opc.credit.amount, Decimal(10 * 1.07).quantize(Decimal('.01')))

    def test_that_saving_order_correction_does_not_alter_the_credit(self):
        order_product = OrderProductFactory.create(amount=10,
                                                   product__base_price=Decimal(1),
                                                   product__order_round__markup_percentage=Decimal(7))

        opc = OrderProductCorrection.objects.create(order_product=order_product,
                                                    supplied_percentage=0)

        self.assertEqual(opc.credit.amount, Decimal(10 * 1.07).quantize(Decimal('.01')))

        opc.supplied_percentage = 10
        opc.save()

        opc = OrderProductCorrection.objects.all().get()
        self.assertEqual(opc.credit.amount, Decimal(10 * 1.07).quantize(Decimal('.01')))

    def test_that_creating_a_correction_creates_sufficient_credit_4(self):
        order_product = OrderProductFactory.create(amount=1,
                                                   product__base_price=Decimal(1),
                                                   product__order_round__markup_percentage=Decimal(7))

        opc = OrderProductCorrection.objects.create(order_product=order_product,
                                                    supplied_percentage=50)

        # Price is 1 Euro, markup is 7%, so total price is 1.07.
        # Half of 1.07 is 0.535
        # Rounding is ROUND_DOWN to 2 decimals, so 0.53.

        self.assertEqual(opc.credit.amount, Decimal('0.53'))

    def test_that_creating_a_correction_creates_sufficient_credit_5(self):
        order_product = OrderProductFactory.create(amount=2,
                                                   product__base_price=Decimal(1),
                                                   product__order_round__markup_percentage=Decimal(7))

        opc = OrderProductCorrection.objects.create(order_product=order_product,
                                                    supplied_percentage=45)

        # Price is 1 Euro, markup is 7%, amount is 2, so total price is 2.14.
        # 0.9 supplied, so 1.1 was not supplied.
        # 1.07 * 1.1 = 1.177
        # Rounding is ROUND_DOWN to 2 decimals, so 1.17.

        self.assertEqual(opc.credit.amount, Decimal('1.17'))

    def test_that_credit_description_is_filled_in(self):
        order_product = OrderProductFactory.create()
        opc = OrderProductCorrection.objects.create(order_product=order_product,
                                                    supplied_percentage=0)
        self.assertEqual(opc.credit.notes, "Correctie in ronde %d, %dx %s, geleverd: %s%%" %
                         (opc.order_product.product.order_round.id,
                          opc.order_product.amount,
                          opc.order_product.product.name,
                          opc.supplied_percentage))
