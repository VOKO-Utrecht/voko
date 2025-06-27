from django.core.management.base import BaseCommand
from constance import config
from ordering.core import create_orderround_automatically, should_create_new_orderround


class Command(BaseCommand):
    help = "Create a new order round automatically based on configuration"

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force creation even if automation is disabled or not needed",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be created without actually creating it",
        )

    def handle(self, *args, **options):
        if options["dry_run"]:
            self.stdout.write("=== DRY RUN MODE ===")

        # Check current configuration
        self.stdout.write(f"Auto-creation enabled: {config.AUTO_CREATE_ORDERROUNDS}")
        self.stdout.write(f"Interval: {config.ORDERROUND_INTERVAL_WEEKS} weeks")
        self.stdout.write(f"Open hour: {config.ORDERROUND_OPEN_HOUR}:00")
        self.stdout.write(f"Duration: {config.ORDERROUND_DURATION_HOURS} hours")
        self.stdout.write(f"Collect days after: {config.ORDERROUND_COLLECT_DAYS_AFTER}")
        self.stdout.write(f"Collect hour: {config.ORDERROUND_COLLECT_HOUR}:00")
        self.stdout.write(f"Create days ahead: {config.ORDERROUND_CREATE_DAYS_AHEAD}")
        if hasattr(config, "ORDERROUND_DEFAULT_TRANSPORT_COORDINATOR"):
            self.stdout.write(f"Default transport coordinator: {config.ORDERROUND_DEFAULT_TRANSPORT_COORDINATOR}")
        if hasattr(config, "ORDERROUND_DEFAULT_PICKUP_LOCATION"):
            self.stdout.write(f"Default pickup location: {config.ORDERROUND_DEFAULT_PICKUP_LOCATION}")

        # Check if creation is needed
        should_create = should_create_new_orderround(config.ORDERROUND_CREATE_DAYS_AHEAD)
        self.stdout.write(f"Should create new round: {should_create}")

        if not should_create and not options["force"]:
            self.stdout.write(self.style.WARNING("No new order round needed. Use --force to create anyway."))
            return

        if not config.AUTO_CREATE_ORDERROUNDS and not options["force"]:
            self.stdout.write(self.style.WARNING("Auto-creation is disabled. Use --force to create anyway."))
            return

        if options["dry_run"]:
            from ordering.core import calculate_next_orderround_dates

            open_dt, close_dt, collect_dt = calculate_next_orderround_dates(
                interval_weeks=config.ORDERROUND_INTERVAL_WEEKS,
                open_hour=config.ORDERROUND_OPEN_HOUR,
                close_hour=config.ORDERROUND_CLOSE_HOUR,
                duration_hours=config.ORDERROUND_DURATION_HOURS,
                collect_days_after=config.ORDERROUND_COLLECT_DAYS_AFTER,
                collect_hour=config.ORDERROUND_COLLECT_HOUR,
            )

            self.stdout.write("Would create order round with:")
            self.stdout.write(f"  Open: {open_dt}")
            self.stdout.write(f"  Close: {close_dt}")
            self.stdout.write(f"  Collect: {collect_dt}")
            self.stdout.write(f"  Markup: {config.MARKUP_PERCENTAGE}%")
            return

        # Create the order round
        try:
            order_round = create_orderround_automatically()
            if order_round:
                self.stdout.write(self.style.SUCCESS(f"Successfully created order round #{order_round.pk}"))
                self.stdout.write(f"  Opens: {order_round.open_for_orders}")
                self.stdout.write(f"  Closes: {order_round.closed_for_orders}")
                self.stdout.write(f"  Collect: {order_round.collect_datetime}")
                self.stdout.write(f"  Markup: {order_round.markup_percentage}%")
            else:
                self.stdout.write(self.style.WARNING("No order round was created (check logs for details)"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to create order round: {str(e)}"))
            raise
