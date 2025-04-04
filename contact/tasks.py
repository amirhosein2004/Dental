from celery import shared_task
from utils.common_imports import timezone
from datetime import timedelta
from .models import ContactMessage

@shared_task
def delete_old_messages(days=180):
    """
    A Celery task to delete old contact messages from the database.

    Args:
        days (int): The number of days to consider a message old. Defaults to 180 days.

    Returns:
        str: A message indicating the number of deleted messages.
    """
    # Calculate the threshold date
    threshold = timezone.now() - timedelta(days=days)
    
    # Filter messages older than the threshold date
    old_messages = ContactMessage.objects.filter(created_at__lt=threshold)
    
    # Count the number of old messages
    count = old_messages.count()
    
    # Delete the old messages
    old_messages.delete()
    
    # Return a message indicating the number of deleted messages
    return f"Deleted {count} old messages."