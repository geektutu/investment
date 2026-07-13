export default defineNuxtConfig({
  app: {
    head: {
      title: '投资小兔兔',
      meta: [
        { charset: 'UTF-8' },
        { name: 'viewport', content: 'width=device-width, initial-scale=1.0' },
      ],
      link: [
        { rel: 'icon', type: 'image/png', href: '/rabbit.png' },
      ],
    },
  },
  ssr: false,
  css: ['~/style.css'],
  compatibilityDate: '2024-11-01',
})
