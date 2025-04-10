document.addEventListener('DOMContentLoaded', function () {
    const sidebarItems = document.querySelectorAll('.sidebar li');
    const mainContent = document.getElementById('main-content');

    // Manejar clics en la barra lateral
    sidebarItems.forEach(item => {
        item.addEventListener('click', function () {
            // Quitar la clase "active" de todos los elementos
            sidebarItems.forEach(i => i.classList.remove('active'));
            // Agregar la clase "active" al elemento clicado
            this.classList.add('active');

            // Obtener la página a cargar desde el atributo data-page
            const page = this.getAttribute('data-page');

            // Construir la URL del archivo HTML
            const url = `/settings/${page}/`;

            // Usar fetch para cargar el contenido del archivo HTML
            fetch(url)
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`Error al cargar ${url}: ${response.statusText}`);
                    }
                    return response.text();
                })
                .then(html => {
                    // Insertar el contenido HTML en el contenedor principal
                    mainContent.innerHTML = html;
                })
                .catch(error => {
                    console.error(error);
                    mainContent.innerHTML = `<p>Error al cargar la página.</p>`;
                });
        });
    });
});