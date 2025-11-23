console.log("pagos.js cargado correctamente");

document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('form-metodo-pago');
  if (!form) {
    console.warn("No se detectó el formulario de método de pago");
    return;
  }

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    const metodo = document.getElementById('metodo').value;

    if (!metodo) {
      Swal.fire({
        icon: 'warning',
        title: 'Seleccioná un método de pago',
        confirmButtonColor: '#3085d6',
      });
      return;
    }

    Swal.fire({
      title: `¿Confirmar método: ${metodo}?`,
      icon: 'question',
      showCancelButton: true,
      confirmButtonText: 'Sí, continuar',
      cancelButtonText: 'Cancelar',
      confirmButtonColor: '#198754',
      cancelButtonColor: '#6c757d',
      reverseButtons: true,
    }).then((result) => {
      if (result.isConfirmed) {
        form.submit();
      }
    });
  });
});
