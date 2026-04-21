document.addEventListener('DOMContentLoaded', function() {
  const container = document.querySelector('#toolbar');
  const filterPanel = document.getElementById('changelist-filter');
  
  if (container && filterPanel) {
    filterPanel.style.display = 'none';
    // Aseguramos la posición relativa del contenedor
    container.style.position = 'relative';
    
    // Crear botón y asignar ID
    const toggleBtn = document.createElement('button');
    toggleBtn.id = 'toggle-filters-btn'; // <-- ID asignado
    toggleBtn.innerHTML = 'Ocultar Filtros';
    toggleBtn.type = 'button';
    
    container.appendChild(toggleBtn);
    
    // Lógica de colapso
    toggleBtn.addEventListener('click', function(e) {
      e.preventDefault();
      const isHidden = filterPanel.style.display === 'none';
      filterPanel.style.display = isHidden ? 'block' : 'none';
      toggleBtn.innerHTML = isHidden ? 'Ocultar Filtros' : 'Ver Filtros';
    });
  }
  
  setTimeout(function() {
    const tabGestion = document.querySelector('#tablink-historial-de-gestion');
    if (tabGestion) {
      tabGestion.click();
    }
  }, 100);
});
