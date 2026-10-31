export function sumMoney(values) {
  const cents = values.reduce((a, v) => a + Math.round(parseFloat(v) * 100), 0)
  return (cents / 100).toFixed(2)
}