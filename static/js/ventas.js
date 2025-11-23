console.log("ventas.js cargado correctamente");

document.addEventListener('DOMContentLoaded', () => {
  // 🔴 Confirmación para finalizar compra
  const finalizarForm = document.getElementById('form-finalizar-compra');
  if (finalizarForm) {
    console.log("Formulario de finalizar compra detectado");
    finalizarForm.addEventListener('submit', function (e) {
      e.preventDefault();

      Swal.fire({
        title: '¿Finalizar compra?',
        text: 'Se generarán los pedidos y se vaciará tu carrito.',
        icon: 'question',
        showCancelButton: true,
        confirmButtonText: 'Sí, finalizar',
        cancelButtonText: 'Cancelar',
        confirmButtonColor: '#198754',
        cancelButtonColor: '#6c757d',
        reverseButtons: true,
      }).then((result) => {
        if (result.isConfirmed) {
          finalizarForm.submit();
        }
      });
    });
  } else {
    console.warn("No se detectó el formulario de finalizar compra");
  }

  // 🗑️ Botones de eliminar pedido
  const deleteButtons = document.querySelectorAll('.btn-delete');
  if (deleteButtons.length > 0) {
    deleteButtons.forEach(btn => {
      const deleteUrl = btn.dataset.deleteUrl;
      const pedidoId = btn.dataset.pedidoId;

      if (!deleteUrl || !pedidoId) {
        console.warn("Botón eliminar sin datos:", btn);
        return;
      }

      btn.addEventListener('click', () => {
        Swal.fire({
          title: `¿Eliminar pedido #${pedidoId}?`,
          text: 'Esta acción no se puede deshacer.',
          icon: 'warning',
          showCancelButton: true,
          confirmButtonText: 'Sí, eliminar',
          cancelButtonText: 'Cancelar',
          confirmButtonColor: '#d33',
          cancelButtonColor: '#6c757d',
          reverseButtons: true,
        }).then((result) => {
          if (result.isConfirmed) {
            window.location.href = deleteUrl;
          }
        });
      });
    });
  }

  // ✅ Botones de entregar pedido
  const entregarButtons = document.querySelectorAll('.btn-entregar');
  if (entregarButtons.length > 0) {
    entregarButtons.forEach(btn => {
      const pedidoId = btn.dataset.id;

      if (!pedidoId) {
        console.warn("Botón entregar sin data-id:", btn);
        return;
      }

      const entregarUrl = `/ventas/pedidos/${pedidoId}/entregar/`;
      console.log("Entregar →", entregarUrl);

      btn.addEventListener('click', () => {
        Swal.fire({
          title: `¿Marcar pedido #${pedidoId} como entregado?`,
          text: 'El estado del pedido cambiará a ENTREGADO.',
          icon: 'question',
          showCancelButton: true,
          confirmButtonText: 'Sí, marcar entregado',
          cancelButtonText: 'Cancelar',
          confirmButtonColor: '#198754',
          cancelButtonColor: '#6c757d',
          reverseButtons: true,
        }).then((result) => {
          if (result.isConfirmed) {
            window.location.href = entregarUrl;
          }
        });
      });
    });
  }
});
