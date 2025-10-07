// theme/tailwind.config.js

module.exports = {
  content: [
      '../templates/**/*.html',       // Le dice a Tailwind que busque clases en tu carpeta de templates principal
      '../**/templates/**/*.html',    // También busca en las carpetas de templates de otras apps
      '../**/*.py'                    // Busca en todos los archivos Python
  ],
  theme: {
    extend: {},
  },
  plugins: [
    require('daisyui'), // Activa el plugin de daisyUI que instalamos
  ],
}