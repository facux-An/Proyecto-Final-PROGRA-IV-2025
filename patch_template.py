"""
Script para reemplazar la galería de portadas con el nuevo sistema de reordenamiento 1-to-N
"""
from pathlib import Path

template_path = Path(r"c:\Users\fandr\Desktop\biblioteca_plus\productos\templates\productos\producto_form.html")

content = template_path.read_text(encoding='utf-8')

# Extraer el bloque entre <div class="col-md-12 border-top pt-4 mt-2"> y el final del div de portadas
import re
pattern = r'(<div class="col-md-12 border-top pt-4 mt-2">\s*<label class="form-label fs-5 mb-3">Imágenes del Producto</label>).*?(</div>\s*</div>\s*<div class="d-flex flex-column flex-md-row gap-3 mt-5">)'

new_block = """<div class="col-md-12 border-top pt-4 mt-2">
                <label class="form-label fs-5 mb-3">Imágenes del Producto</label>

                {% if form.instance.pk and form.instance.portadas.all %}
                  <div class="mb-4">
                    <div class="d-flex justify-content-between align-items-end mb-3">
                      <p class="text-muted small mb-0">
                        <i class="bi bi-info-circle me-1"></i>
                        Las fotos se muestran en este orden. La primera es la <strong>portada principal</strong>.
                      </p>
                      <button type="button" class="btn btn-sm btn-outline-primary fw-bold" id="btn-activar-reorden" onclick="activarReorden()">
                        <i class="bi bi-arrow-down-up me-1"></i>Reordenar Fotos
                      </button>
                    </div>

                    <!-- Panel de Reordenamiento Activo (Oculto por defecto) -->
                    <div id="panel-reorden" class="alert alert-primary rounded-3 p-3 mb-3 d-none border border-primary">
                      <div class="d-flex justify-content-between align-items-center">
                        <div>
                          <h6 class="fw-bold mb-1 text-primary"><i class="bi bi-hand-index-thumb me-1"></i>Modo Selección</h6>
                          <p class="small mb-0 opacity-75">Hacé clic en las fotos en el orden que querés (1, 2, 3...).</p>
                        </div>
                        <div class="d-flex gap-2">
                          <button type="button" class="btn btn-sm btn-light fw-bold text-secondary" onclick="limpiarOrden()">
                            Limpiar
                          </button>
                          <button type="button" class="btn btn-sm btn-primary fw-bold" onclick="guardarOrden(this)" id="btn-guardar-orden" disabled>
                            Guardar Orden
                          </button>
                        </div>
                      </div>
                    </div>

                    <div class="d-flex flex-wrap gap-3" id="galeria-portadas">
                      {% for portada in form.instance.portadas.all %}
                      <div class="portada-card position-relative text-center" 
                           id="portada-card-{{ portada.id }}" 
                           data-id="{{ portada.id }}"
                           style="width: 130px; transition: transform 0.2s; cursor: default;">
                        
                        <div class="position-relative d-inline-block img-container">
                          <img src="{{ portada.imagen.url }}" alt="Portada {{ forloop.counter }}"
                               style="width: 130px; height: 130px; object-fit: cover; border-radius: 0.75rem;
                                      border: 3px solid {% if forloop.first %}var(--brand-primary){% else %}#e9ecef{% endif %}; display: block;">
                          
                          <!-- Badge Principal Estático -->
                          <span class="badge-principal position-absolute top-0 start-50 translate-middle badge rounded-pill text-white"
                                style="background: var(--brand-primary); font-size: 0.6rem; white-space: nowrap; {% if not forloop.first %}display: none;{% endif %}">
                            ⭐ PRINCIPAL
                          </span>

                          <!-- Badge Numérico de Selección (Oculto por defecto) -->
                          <span class="badge-seleccion position-absolute top-50 start-50 translate-middle badge rounded-circle text-white d-none shadow"
                                style="background: var(--brand-primary); width: 40px; height: 40px; font-size: 1.2rem; line-height: 28px; border: 3px solid white;">
                          </span>
                        </div>
                        
                        <!-- Controles Normales (Se ocultan en modo reorden) -->
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

                  // ── Lógica de Reordenamiento 1-to-N ──────────────────
                  let ordenSeleccion = [];
                  let modoReorden = false;

                  function activarReorden() {
                    modoReorden = true;
                    ordenSeleccion = [];
                    
                    document.getElementById('btn-activar-reorden').classList.add('d-none');
                    document.getElementById('panel-reorden').classList.remove('d-none');
                    document.getElementById('btn-guardar-orden').disabled = true;
                    
                    const cards = document.querySelectorAll('.portada-card');
                    cards.forEach(card => {
                      // Ocultar controles y badges normales
                      card.querySelector('.controles-normales').classList.add('d-none');
                      card.querySelector('.badge-principal').classList.add('d-none');
                      
                      // Efecto visual de "clickeame"
                      const img = card.querySelector('img');
                      img.style.cursor = 'pointer';
                      img.style.opacity = '0.7';
                      img.style.borderColor = '#dee2e6';
                      card.style.transform = 'scale(0.95)';
                      
                      // Remover event listeners anteriores clonando
                      const newCard = card.cloneNode(true);
                      card.parentNode.replaceChild(newCard, card);
                      
                      // Agregar listener de selección
                      newCard.addEventListener('click', () => {
                        seleccionarFoto(newCard);
                      });
                    });
                  }

                  function seleccionarFoto(card) {
                    if (!modoReorden) return;
                    
                    const id = parseInt(card.getAttribute('data-id'));
                    
                    // Si ya está seleccionada, ignorar (o podríamos deseleccionarla)
                    if (ordenSeleccion.includes(id)) return;
                    
                    ordenSeleccion.push(id);
                    const numero = ordenSeleccion.length;
                    
                    // Actualizar UI de la foto
                    const img = card.querySelector('img');
                    img.style.opacity = '1';
                    img.style.borderColor = 'var(--brand-primary)';
                    card.style.transform = 'scale(1.05)';
                    
                    const badge = card.querySelector('.badge-seleccion');
                    badge.textContent = numero;
                    badge.classList.remove('d-none');
                    
                    // Habilitar botón de guardar si todas las fotos están seleccionadas
                    const totalFotos = document.querySelectorAll('.portada-card').length;
                    if (ordenSeleccion.length === totalFotos) {
                      document.getElementById('btn-guardar-orden').disabled = false;
                    }
                  }

                  function limpiarOrden() {
                    ordenSeleccion = [];
                    document.getElementById('btn-guardar-orden').disabled = true;
                    
                    document.querySelectorAll('.portada-card').forEach(card => {
                      const img = card.querySelector('img');
                      img.style.opacity = '0.7';
                      img.style.borderColor = '#dee2e6';
                      card.style.transform = 'scale(0.95)';
                      card.querySelector('.badge-seleccion').classList.add('d-none');
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
                        btn.innerHTML = 'Guardar Orden';
                      }
                    } catch(e) {
                      alert('Error de conexión.');
                      btn.disabled = false;
                      btn.innerHTML = 'Guardar Orden';
                    }
                  }
                </script>
              </div>\n"""

new_content = re.sub(pattern, new_block + r'\2', content, flags=re.DOTALL)

template_path.write_text(new_content, encoding='utf-8')
print("Template updated correctly.")
