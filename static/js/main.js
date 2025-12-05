/**
 * Main JavaScript file for WhatsApp CRM
 */

// Initialize Bootstrap components
document.addEventListener('DOMContentLoaded', function() {
  // Initialize all tooltips
  const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
  tooltipTriggerList.map(function(tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });

  // Initialize all popovers
  const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
  popoverTriggerList.map(function(popoverTriggerEl) {
    return new bootstrap.Popover(popoverTriggerEl);
  });

  // Auto-dismiss alerts after 5 seconds
  setTimeout(function() {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
      const bsAlert = new bootstrap.Alert(alert);
      bsAlert.close();
    });
  }, 5000);
});

// Function to format phone numbers as international format
function formatPhoneNumber(input) {
  // Remove all non-digit characters
  let phoneNumber = input.value.replace(/\D/g, '');
  
  // Add + at the beginning if not present
  if (phoneNumber && phoneNumber.charAt(0) !== '+') {
    phoneNumber = '+' + phoneNumber;
  }
  
  // Update the input value
  input.value = phoneNumber;
}

// Add event listeners to phone number inputs
document.addEventListener('DOMContentLoaded', function() {
  const phoneInputs = document.querySelectorAll('input[type="tel"]');
  
  phoneInputs.forEach(function(input) {
    input.addEventListener('blur', function() {
      formatPhoneNumber(this);
    });
  });
});
