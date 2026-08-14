import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from adminapp.models import Admintbl
from hospitalapp.models import Hospitaltbl, Vaccinetbl, Receptionisttbl
from patientapp.models import Patienttbl
from kiddovax.excel_exporter import export_db_to_excel

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Admintbl)
@receiver(post_delete, sender=Admintbl)
@receiver(post_save, sender=Hospitaltbl)
@receiver(post_delete, sender=Hospitaltbl)
@receiver(post_save, sender=Receptionisttbl)
@receiver(post_delete, sender=Receptionisttbl)
@receiver(post_save, sender=Patienttbl)
@receiver(post_delete, sender=Patienttbl)
@receiver(post_save, sender=Vaccinetbl)
@receiver(post_delete, sender=Vaccinetbl)
def trigger_excel_export(sender, instance, **kwargs):
    """
    Triggers the Excel export utility on model creation, update, or deletion.
    Handles exceptions to prevent database transactions from crashing
    if the Excel file is locked (e.g. open in Microsoft Excel).
    """
    try:
        export_db_to_excel()
        logger.info(f"Successfully updated Excel spreadsheet on modification of {sender.__name__} (id={instance.id})")
    except Exception as e:
        logger.error(
            f"Failed to update Excel spreadsheet 'hospital_credentials.xlsx' on change to {sender.__name__}: {e}",
            exc_info=True
        )
