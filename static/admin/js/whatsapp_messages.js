document.addEventListener('DOMContentLoaded', function() {
  const container = document.querySelector('#toolbar');
  const filterPanel = document.getElementById('changelist-filter');
  
  if (container && filterPanel) {
    // Aseguramos la posición relativa del contenedor
    container.style.position = 'relative';
    
    // Crear botón y asignar ID
    const toggleBtn = document.createElement('button');
    toggleBtn.id = 'toggle-filters-btn'; // <-- ID asignado
    toggleBtn.innerHTML = 'Ocultar Filtros';
    toggleBtn.type = 'button';
    
    container.appendChild(toggleBtn);
    
    if (innerWidth >= 768) {
      filterPanel.style.display = 'none';
      toggleBtn.innerHTML = 'Ver Filtros';
    }
    
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
  
  
  // Modal Whatsapp
  const dataElement = document.getElementById('wa-data-json');
  if (!dataElement) return;

  const messages = JSON.parse(dataElement.textContent);

  const modalHtml = `
    <div id="waModal" style="display:none; position:fixed; z-index:9999; left:0; top:0; width:100%; height:100%; background:rgba(0,0,0,0.5); font-family: sans-serif;">
      <div style="background:#fefefe; margin: 10vh auto; padding: 2rem; border: 1px solid #888; max-width: 600px; width: 90%; border-radius: 0.5rem; overflow-y: auto; max-height: 80vh; box-shadow: 0 4px 15px rgba(0,0,0,0.2);">
        <h3 style="margin-top: 0; color: #205493;">Mensajes para WhatsApp</h3>
        <p id="waLeadName" style="font-weight: bold; color: #555;"></p>
        <p style="margin-bottom: 1rem; font-size: 0.9rem; color: #666;">Seleccione un mensaje predeterminado o continúe para escribir uno personalizado.</p>
        <div id="waOptions" style="margin: 15px 0; border: 1px solid #eee; padding: 10px; border-radius: 5px; max-height: 40vh; overflow-y: auto;"></div>
        <div style="text-align:right; margin-top: 20px;">
          <button id="waCancel" class="button" style="background: #ccc; color: black; border: none; padding: 10px 20px; cursor: pointer; border-radius: 4px; margin-right: 5px;">Cancelar</button>
          <button id="waNext" class="button" style="background:#205493; color:white; border: none; padding: 10px 20px; cursor: pointer; border-radius: 4px;">Siguiente</button>
        </div>
      </div>
    </div>
  `;
    
  document.body.insertAdjacentHTML('beforeend', modalHtml);
  
  let currentPhone = "";
  let currentName = "";

  // 2. Evento click en el botón de la tabla
  document.querySelectorAll('.whatsapp-trigger').forEach(btn => {
    btn.addEventListener('click', function(e) {
      e.preventDefault();
      currentPhone = this.dataset.phone;
      currentName = this.dataset.name || ""; // Captura el nombre del data-name
      
      document.getElementById('waLeadName').innerText = `Enviar a: ${currentName}`;
      
      const container = document.getElementById('waOptions');
      container.innerHTML = messages.map(m => `
        <div style="margin-bottom: 12px; border-bottom: 1px solid #eee; padding-bottom: 8px;">
          <label style="cursor:pointer; display: flex; align-items: flex-start;">
            <input type="radio" name="waMsg" value="${m.id}" style="margin-top: 4px; margin-right: 12px;"> 
            <div style="flex: 1;">
              <strong style="display:block; color:#333; font-size: 1rem;">${m.title}</strong>
              <small style="color:#777; line-height: 1.2; display: block; margin-top: 2px;">${m.content.substring(0, 80)}...</small>
            </div>
          </label>
        </div>
      `).join('');
          
      document.getElementById('waModal').style.display = 'block';
    });
  });
        
  // 3. Botón Siguiente
  document.getElementById('waNext').onclick = function() {
    const selectedRadio = document.querySelector('input[name="waMsg"]:checked');
    let url = `https://api.whatsapp.com/send?phone=${currentPhone}`;
    
    if (selectedRadio) {
      const msgId = selectedRadio.value;
      const messageObj = messages.find(m => m.id == msgId);
      
      // Insertamos el saludo personalizado antes del contenido del mensaje
      const fullMessage = `Hola ${currentName}! 👋\n\n${messageObj.content}`;
      const encodedText = encodeURIComponent(fullMessage);
      
      url += `&text=${encodedText}`;
    }
    
    window.open(url, '_blank');
    document.getElementById('waModal').style.display = 'none';
  };  
        
  document.getElementById('waCancel').onclick = () => {
    document.getElementById('waModal').style.display = 'none';
  };

  // Cerrar modal si hacen click fuera del recuadro blanco
  window.onclick = function(event) {
    const modal = document.getElementById('waModal');
    if (event.target == modal) {
      modal.style.display = "none";
    }
  }

});
  