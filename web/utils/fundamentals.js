let cache = null
let cacheUrl = ''

function parse(text) {
  const map = {}
  if (!text) return map
  const lines = text.replace(/^\uFEFF/, '').trim().split('\n')
  const headers = lines[0].split(',').map(h => h.trim())
  const codeIdx = headers.indexOf('代码')
  const priceIdx = headers.indexOf('最新价')
  const peIdx = headers.indexOf('PE(TTM)')
  const roeIdx = headers.indexOf('ROE(TTM)')
  const growthIdx = headers.indexOf('净利同比')
  if (codeIdx === -1) return map
  for (let i = 1; i < lines.length; i++) {
    const cols = lines[i].split(',')
    const code = cols[codeIdx]?.trim()
    if (!code) continue
    map[code] = {
      price: priceIdx === -1 ? '' : cols[priceIdx]?.trim(),
      pe: peIdx === -1 ? '' : cols[peIdx]?.trim(),
      roe: roeIdx === -1 ? '' : cols[roeIdx]?.trim(),
      growth: growthIdx === -1 ? '' : cols[growthIdx]?.trim(),
    }
  }
  return map
}

// 全站共享一次请求，返回 { 代码: { pe, roe, growth } }
export function loadFundamentals(baseURL) {
  const url = `${baseURL}data/stock_fundamental.csv`
  if (!cache || cacheUrl !== url) {
    cacheUrl = url
    cache = fetch(url)
      .then(res => (res.ok ? res.text() : ''))
      .then(parse)
      .catch(() => ({}))
  }
  return cache
}
