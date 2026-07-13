const baseURL = '/investment/'

export default defineNuxtConfig({
  app: {
    baseURL,
    head: {
      title: '投资小兔兔',
      meta: [
        { charset: 'UTF-8' },
        { name: 'viewport', content: 'width=device-width, initial-scale=1.0' },
      ],
      link: [
        { rel: 'icon', type: 'image/png', href: `${baseURL}rabbit.png` },
      ],
    },
  },
  ssr: false,
  css: ['~/style.css'],
  appConfig: {
    buildTime: new Date().toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai' }),
  },
  compatibilityDate: '2024-11-01',
})
