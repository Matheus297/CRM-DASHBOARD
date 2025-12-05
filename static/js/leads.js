/**
 * JavaScript for the leads functionality
 */

document.addEventListener('DOMContentLoaded', function() {
  // Handle lead search form
  const searchForm = document.querySelector('form[action*="search_leads"]');
  if (searchForm) {
    searchForm.addEventListener('submit', function(e) {
      const queryInput = searchForm.querySelector('input[name="query"]');
      const dateInput = searchForm.querySelector('input[name="date"]');
      
      // Only submit if at least one field has a value
      if (!queryInput.value && !dateInput.value) {
        e.preventDefault();
        window.location.href = '/leads';
      }
    });
    
    // Clear search button functionality
    const clearBtn = document.getElementById('clear-search');
    if (clearBtn) {
      clearBtn.addEventListener('click', function() {
        window.location.href = '/leads';
      });
    }
  }
  
  // Format date in table cells for better readability
  const dateCells = document.querySelectorAll('td[data-date]');
  dateCells.forEach(function(cell) {
    const dateValue = cell.getAttribute('data-date');
    if (dateValue) {
      const date = new Date(dateValue);
      cell.textContent = date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
    } else {
      cell.textContent = 'None';
    }
  });
});
