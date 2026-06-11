"""
Script para reemplazar la galería de portadas con el nuevo sistema directo de checkboxes 1-to-N
"""
from pathlib import Path

template_path = Path(r"c:\Users\fandr\Desktop\biblioteca_plus\productos\templates\productos\producto_form.html")
content = template_path.read_text(encoding='utf-8')

import re
pattern = r'(<div class="col-md-12 border-top pt-4 mt-2">\s*<label class="form-label fs-5 mb-3">Imágenes del Producto</label>).*?(</div>\s*</div>\s*<div class="d-flex flex-column flex-md-row gap-3 mt-5">)'

new_block = """<div class="col-md-12 border-top pt-4 mt-2">
                <label class="form-label fs-5 mb-3">Imágenes del Producto</label>

                {% if form.instance.pk and form.instance.portadas.all %}
                  <div class="mb-4">
                    <p class="text-muted small mb-3">
                      <i class="bi bi-info-circle me-1"></i>
                      Tocá el cuadradito de las fotos en el orden que prefieras (1, 2, 3...) para reordenarlas. La primera será la <strong>portada principal</strong>.
                    </p>

                    <div class="d-flex flex-wrap gap-3" id="galeria-portadas">
                      {% for portada in form.instance.portadas.all %}
                      <div class="portada-card position-relative text-center" 
                           id="portada-card-{{ portada.id }}" 
                           data-id="{{ portada.id }}"
                           style="width: 130px; transition: transform 0.2s;">
                        
                        <div class="position-relative d-inline-block img-container">
                          <!-- Checkbox / Cuadradito Directo (Top Left) -->
                          <div class="checkbox-orden position-absolute top-0 start-0 m-1 rounded shadow-sm d-flex align-items-center justify-content-center"
                               onclick="seleccionarFoto({{ portada.id }}, this)"
                               style="width: 32px; height: 32px; background: rgba(255,255,255,0.9); border: 2px solid #ccc; cursor: pointer; z-index: 10; font-weight: bold; font-size: 1rem; color: var(--brand-primary); transition: all 0.2s;">
                          </div>

                          <img src="{{ portada.imagen.url }}" alt="Portada {{ forloop.counter }}"
                               style="width: 130px; height: 130px; object-fit: cover; border-radius: 0.75rem;
                                      border: 3px solid {% if forloop.first %}var(--brand-primary){% else %}#e9ecef{% endif %}; display: block;">
                          
                          <!-- Badge Principal Estático -->
                          <span class="badge-principal position-absolute top-0 start-50 translate-middle badge rounded-pill text-white"
                                style="background: var(--brand-primary); font-size: 0.6rem; white-space: nowrap; {% if not forloop.first %}display: none;{% endif %}">
                            ⭐ PRINCIPAL
                          </span>
                        </div>
                        
                        <!-- Controles Normales (Botón Eliminar) -->
                        <div class="controles-normales d-flex gap-1 mt-2 justify-content-center">
                          <button type="button"
                                  onclick="eliminarPortada({{ portada.id }}, this)"
                                  class="btn btn-sm btn-outline-danger rounded-pill fw-bold w-100"
                                  style="font-size: 0.7rem; padding: 3px 8px;"
                                  title="Eliminar imagen">
                            <i class="bi bi-trash3 me-1"></i>Eliminar
                          </button>
                        </div>
                      </div>
                      {% endfor %}
                    </div>

                    <!-- Panel de Guardado (Oculto hasta que se seleccione algo) -->
                    <div id="panel-guardar-orden" class="mt-3 p-3 bg-light rounded-3 border d-none align-items-center justify-content-between">
                      <div>
                        <span class="fw-bold text-primary"><i class="bi bi-check2-circle me-1"></i>Nuevo orden detectado</span>
                        <br><span class="small text-muted">¿Guardar los cambios?</span>
                      </div>
                      <div class="d-flex gap-2">
                        <button type="button" class="btn btn-sm btn-outline-secondary fw-bold" onclick="limpiarOrden()">
                          Limpiar
                        </button>
                        <button type="button" class="btn btn-sm btn-primary fw-bold" onclick="guardarOrden(this)">
                          Guardar Nuevo Orden
                        </button>
                      </div>
                    </div>
                  </div>
                {% endif %}

                <div class="multi-upload mt-4">
                  <i class="bi bi-cloud-arrow-up mb-2"></i>
                  <h6 class="fw-bold mb-1">{% if form.instance.pk %}Agregar más imágenes{% else %}Imágenes del producto{% endif %} (hasta 5)</h6>
                  <p class="small text-muted mb-3">Formatos aceptados: JPG, PNG, WEBP.</p>
                  {{ portadas_form.portadas }}
                </div>
                {% if portadas_form.portadas.errors %}
                  <div class="text-danger small mt-2 fw-bold text-center">{{ portadas_form.portadas.errors|striptags }}</div>
                {% endif %}

                <script>
                  const CSRF_TOKEN = document.querySelector('[name=csrfmiddlewaretoken]').value;
                  const productoId = '{{ form.instance.pk }}';
                  
                  // Lógica de Eliminación (Igual que antes)
                  async function eliminarPortada(portadaId, btn) {
                    if (!confirm('¿Seguro que querés eliminar esta imagen?')) return;
                    btn.disabled = true;
                    btn.innerHTML = '<i class="bi bi-hourglass-split"></i>';
                    try {
                      const res = await fetch('/productos/portada/' + portadaId + '/eliminar/', {
                        method: 'POST',
                        headers: { 'X-CSRFToken': CSRF_TOKEN }
                      });
                      const data = await res.json();
                      if (data.ok) {
                        const card = document.getElementById('portada-card-' + portadaId);
                        card.style.opacity = '0';
                        setTimeout(() => card.remove(), 300);
                      } else {
                        alert(data.error || 'No se pudo eliminar la imagen.');
                        btn.disabled = false;
                        btn.innerHTML = '<i class="bi bi-trash3 me-1"></i>Eliminar';
                      }
                    } catch(e) {
                      alert('Error de conexión.');
                      btn.disabled = false;
                      btn.innerHTML = '<i class="bi bi-trash3 me-1"></i>Eliminar';
                    }
                  }

                  // ── Lógica de Reordenamiento Directo 1-to-N ──────────────────
                  let ordenSeleccion = [];

                  function seleccionarFoto(id, checkboxDiv) {
                    // Si ya está seleccionada, ignoramos (para destildar habría que usar "Limpiar")
                    if (ordenSeleccion.includes(id)) return;
                    
                    ordenSeleccion.push(id);
                    const numero = ordenSeleccion.length;
                    
                    // Actualizar UI del checkbox
                    checkboxDiv.style.background = 'var(--brand-primary)';
                    checkboxDiv.style.borderColor = 'var(--brand-primary)';
                    checkboxDiv.style.color = 'white';
                    checkboxDiv.textContent = numero;
                    
                    // Efecto visual en la tarjeta
                    const card = document.getElementById('portada-card-' + id);
                    const img = card.querySelector('img');
                    img.style.borderColor = 'var(--brand-primary)';
                    card.style.transform = 'scale(1.05)';
                    
                    // Mostrar panel de guardado
                    document.getElementById('panel-guardar-orden').classList.remove('d-none');
                    document.getElementById('panel-guardar-orden').classList.add('d-flex');
                  }

                  function limpiarOrden() {
                    ordenSeleccion = [];
                    
                    // Ocultar panel de guardado
                    document.getElementById('panel-guardar-orden').classList.add('d-none');
                    document.getElementById('panel-guardar-orden').classList.remove('d-flex');
                    
                    // Resetear UI de todas las tarjetas
                    document.querySelectorAll('.portada-card').forEach(card => {
                      const img = card.querySelector('img');
                      const isFirst = card.querySelector('.badge-principal') && !card.querySelector('.badge-principal').classList.contains('d-none');
                      
                      img.style.borderColor = isFirst ? 'var(--brand-primary)' : '#e9ecef';
                      card.style.transform = 'scale(1)';
                      
                      const checkbox = card.querySelector('.checkbox-orden');
                      checkbox.style.background = 'rgba(255,255,255,0.9)';
                      checkbox.style.borderColor = '#ccc';
                      checkbox.style.color = 'var(--brand-primary)';
                      checkbox.textContent = '';
                    });
                  }

                  async function guardarOrden(btn) {
                    btn.disabled = true;
                    btn.innerHTML = '<i class="bi bi-hourglass-split me-1"></i>Guardando...';
                    
                    try {
                      const res = await fetch(`/productos/${productoId}/reordenar-portadas/`, {
                        method: 'POST',
                        headers: { 
                          'X-CSRFToken': CSRF_TOKEN,
                          'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ orden_ids: ordenSeleccion })
                      });
                      
                      const data = await res.json();
                      if (data.ok) {
                        location.reload(); // Recargar para ver el nuevo orden aplicado desde BD
                      } else {
                        alert(data.error || 'No se pudo guardar el orden.');
                        btn.disabled = false;
                        btn.innerHTML = 'Guardar Nuevo Orden';
                      }
                    } catch(e) {
                      alert('Error de conexión.');
                      btn.disabled = false;
                      btn.innerHTML = 'Guardar Nuevo Orden';
                    }
                  }
                </script>
              </div>\n"""

new_content = re.sub(pattern, new_block + r'\2', content, flags=re.DOTALL)
template_path.write_text(new_content, encoding='utf-8')
print("Template updated correctly.")
