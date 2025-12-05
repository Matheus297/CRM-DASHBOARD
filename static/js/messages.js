/**
 * JavaScript for the message functionality
 */

document.addEventListener('DOMContentLoaded', function() {
  // Toggle lead select based on bulk message checkbox
  const bulkCheckbox = document.getElementById('is_bulk');
  const leadSelectDiv = document.getElementById('lead_select_div');
  
  if (bulkCheckbox && leadSelectDiv) {
    bulkCheckbox.addEventListener('change', function() {
      if (this.checked) {
        leadSelectDiv.style.display = 'none';
        document.getElementById('lead_id').value = '';
      } else {
        leadSelectDiv.style.display = 'block';
      }
    });
  }
  
  // Set min datetime for scheduled message to current time
  const scheduledTimeInput = document.getElementById('scheduled_time');
  if (scheduledTimeInput) {
    // Get current date and time
    const now = new Date();
    
    // Format date and time for datetime-local input
    // YYYY-MM-DDThh:mm
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const day = String(now.getDate()).padStart(2, '0');
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    
    const formattedDateTime = `${year}-${month}-${day}T${hours}:${minutes}`;
    
    // Set min attribute
    scheduledTimeInput.setAttribute('min', formattedDateTime);
    
    // Default to 30 minutes from now
    const thirtyMinsLater = new Date(now.getTime() + 30 * 60000);
    const laterHours = String(thirtyMinsLater.getHours()).padStart(2, '0');
    const laterMinutes = String(thirtyMinsLater.getMinutes()).padStart(2, '0');
    
    const suggestedDateTime = `${year}-${month}-${day}T${laterHours}:${laterMinutes}`;
    scheduledTimeInput.value = suggestedDateTime;
  }
  
  // Template select functionality
  const templateSelect = document.getElementById('template_select');
  const messageTextarea = document.getElementById('message');
  
  if (templateSelect && messageTextarea) {
    templateSelect.addEventListener('change', function() {
      if (this.value) {
        // If current textarea has content, confirm before overwriting
        if (messageTextarea.value.trim() && !confirm('Isso substituirá o texto atual da mensagem. Continuar?')) {
          // Reset select to placeholder if user cancels
          this.selectedIndex = 0;
          return;
        }
        messageTextarea.value = this.value;
        // Trigger input event to update character counter if present
        messageTextarea.dispatchEvent(new Event('input'));
      }
    });
  }
  
  // Character counter for message textarea
  const charCounter = document.getElementById('char-counter');
  
  if (messageTextarea && charCounter) {
    messageTextarea.addEventListener('input', function() {
      const count = this.value.length;
      charCounter.textContent = count + ' caracteres';
      
      // Limite de caracteres para lembretes (mantendo 4000 como boas práticas)
      if (count > 4000) {
        charCounter.classList.add('text-danger');
      } else {
        charCounter.classList.remove('text-danger');
      }
    });
    
    // Initial count
    const initialCount = messageTextarea.value.length;
    charCounter.textContent = initialCount + ' caracteres';
  }
});
