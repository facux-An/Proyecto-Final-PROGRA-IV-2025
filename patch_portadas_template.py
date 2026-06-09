"""
Script de parche: reemplaza la seccion de portadas en producto_form.html
con la nueva galería de gestión interactiva.
"""
from pathlib import Path

template_path = Path(r"c:\Users\fandr\Desktop\biblioteca_plus\productos\templates\productos\producto_form.html")

old_block = """              <div class="col-md-12 border-top pt-4 mt-2">
                <label class="form-label fs-5 mb-3">Imágenes del Producto</label>
                
                {% if form.instance.pk and form.instance.imagen_principal_url %}
                  <div class="d-flex align-items-center gap-4 mb-4 bg-light p-3 rounded-4 border">
                    <img src="{{ form.instance.imagen_principal_url }}" alt="Portada" class="preview-img">
                    <div>
                      <h6 class="fw-bold mb-1">Portada Actual</h6>
                      <p class="text-muted small mb-0">Esta es la imagen principal que ven los clientes.</p>
                    </div>
                  </div>
                {% endif %}

                <div class="multi-upload">
                  <i class="bi bi-cloud-arrow-up mb-2"></i>
                  <h6 class="fw-bold mb-1">Subir nuevas imágenes (hasta 5)</h6>
                  <p class="small text-muted mb-3">Formatos aceptados: JPG, PNG, WEBP.</p>
                  {{ portadas_form.portadas }}
                </div>
                {% if portadas_form.portadas.errors %}
                  <div class="text-danger small mt-2 fw-bold text-center">{{ portadas_form.portadas.errors|striptags }}</div>
                {% endif %}
              </div>"""

new_block = """              <div class="col-md-12 border-top pt-4 mt-2">
                <label class="form-label fs-5 mb-3">Imágenes del Producto</label>

                {% if form.instance.pk and form.instance.portadas.all %}
                <!-- ══ GALERÍA INTERACTIVA DE PORTADAS ════════════════════════════════
                     Muestra todas las imágenes del producto con controles AJAX para:
                     - Eliminar una imagen individual (sin borrar las demás)
                     - Establecer cualquier imagen como portada principal
                     La primera imagen (con borde naranja) es siempre la principal
                     (portadas.first() en el modelo usa ORDER BY id ASC). -->
                  <div class="mb-4">
                    <p class="text-muted small mb-2">
                      <i class="bi bi-info-circle me-1"></i>
                      La imagen con borde naranja es la <strong>portada principal</strong> visible para los clientes.
                    </p>
                    <div class="d-flex flex-wrap gap-3" id="galeria-portadas">
                      {% for portada in form.instance.portadas.all %}
                      <div class="portada-card position-relative text-center" id="portada-card-{{ portada.id }}" style="width: 130px;">
                        <div class="position-relative d-inline-block">
                          <img src="{{ portada.imagen.url }}" alt="Portada {{ forloop.counter }}"
                               style="width: 130px; height: 130px; object-fit: cover; border-radius: 0.75rem;
                                      border: 3px solid {% if forloop.first %}var(--brand-primary){% else %}#e9ecef{% endif %}; display: block;">
                          {% if forloop.first %}
                            <span class="position-absolute top-0 start-50 translate-middle badge rounded-pill text-white"
                                  style="background: var(--brand-primary); font-size: 0.6rem; white-space: nowrap;">
                              ⭐ PRINCIPAL
                            </span>
                          {% endif %}
                        </div>
                        <div class="d-flex gap-1 mt-2 justify-content-center">
                          {% if not forloop.first %}
                          <button type="button"
                                  onclick="establecerPrincipal({{ portada.id }}, this)"
                                  class="btn btn-sm btn-outline-warning rounded-pill flex-grow-1 fw-bold"
                                  style="font-size: 0.62rem; padding: 2px 4px;">
                            <i class="bi bi-star-fill"></i> Principal
                          </button>
                          {% endif %}
                          <button type="button"
                                  onclick="eliminarPortada({{ portada.id }}, this)"
                                  class="btn btn-sm btn-outline-danger rounded-pill fw-bold"
                                  style="font-size: 0.62rem; padding: 2px 8px;"
                                  title="Eliminar imagen">
                            <i class="bi bi-trash3"></i>
                          </button>
                        </div>
                      </div>
                      {% endfor %}
                    </div>
                  </div>
                  <div class="alert alert-info rounded-3 p-2 small mb-3">
                    <i class="bi bi-arrow-up-circle me-1"></i>
                    <strong>¿Querés reemplazar todas las imágenes?</strong>
                    Subí nuevas fotos abajo y al guardar se van a reemplazar todas las actuales.
                  </div>
                {% endif %}

                <div class="multi-upload">
                  <i class="bi bi-cloud-arrow-up mb-2"></i>
                  <h6 class="fw-bold mb-1">{% if form.instance.pk %}Subir nuevas imágenes{% else %}Imágenes del producto{% endif %} (hasta 5)</h6>
                  <p class="small text-muted mb-3">Formatos aceptados: JPG, PNG, WEBP. La primera imagen será la portada principal.</p>
                  {{ portadas_form.portadas }}
                </div>
                {% if portadas_form.portadas.errors %}
                  <div class="text-danger small mt-2 fw-bold text-center">{{ portadas_form.portadas.errors|striptags }}</div>
                {% endif %}

                <!-- ── JS: Gestión AJAX de portadas individuales ───────────────────
                     eliminarPortada(): POST a /productos/portada/{id}/eliminar/
                     establecerPrincipal(): POST a /productos/portada/{id}/principal/ -->
                <script>
                  const CSRF_TOKEN = '{{ csrf_token }}';

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
                        card.style.transition = 'opacity 0.3s';
                        card.style.opacity = '0';
                        setTimeout(() => card.remove(), 300);
                      } else {
                        alert(data.error || 'No se pudo eliminar la imagen.');
                        btn.disabled = false;
                        btn.innerHTML = '<i class="bi bi-trash3"></i>';
                      }
                    } catch(e) {
                      alert('Error de conexión.');
                      btn.disabled = false;
                      btn.innerHTML = '<i class="bi bi-trash3"></i>';
                    }
                  }

                  async function establecerPrincipal(portadaId, btn) {
                    btn.disabled = true;
                    btn.innerHTML = '<i class="bi bi-hourglass-split"></i>';
                    try {
                      const res = await fetch('/productos/portada/' + portadaId + '/principal/', {
                        method: 'POST',
                        headers: { 'X-CSRFToken': CSRF_TOKEN }
                      });
                      const data = await res.json();
                      if (data.ok) {
                        location.reload();
                      } else {
                        alert('No se pudo cambiar la portada principal.');
                        btn.disabled = false;
                        btn.innerHTML = '<i class="bi bi-star-fill"></i> Principal';
                      }
                    } catch(e) {
                      alert('Error de conexión.');
                      btn.disabled = false;
                      btn.innerHTML = '<i class="bi bi-star-fill"></i> Principal';
                    }
                  }
                </script>
              </div>"""

content = template_path.read_text(encoding='utf-8')

if old_block in content:
    new_content = content.replace(old_block, new_block, 1)
    template_path.write_text(new_content, encoding='utf-8')
    print("OK: bloque reemplazado correctamente.")
else:
    # Intentar con CRLF
    old_crlf = old_block.replace('\n', '\r\n')
    if old_crlf in content:
        new_content = content.replace(old_crlf, new_block, 1)
        template_path.write_text(new_content, encoding='utf-8')
        print("OK: bloque CRLF reemplazado correctamente.")
    else:
        print("ERROR: No se encontró el bloque exacto. Revisa manualmente.")
        # Mostrar las líneas 174-196 para diagnóstico
        lines = content.splitlines()
        for i, line in enumerate(lines[173:196], start=174):
            print(f"{i}: {repr(line)}")
