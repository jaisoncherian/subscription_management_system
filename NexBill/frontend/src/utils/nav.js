export const NAV = [
  { to: '/dashboard', label: 'Dashboard', icon: '📊', roles: ['admin', 'staff'] },
  { to: '/subscriptions', label: 'Subscriptions', icon: '🔁', roles: ['admin', 'staff'] },
  { to: '/invoices', label: 'Invoices', icon: '🧾', roles: ['admin', 'staff'] },
  { to: '/payments', label: 'Payments', icon: '💳', roles: ['admin', 'staff'] },
  { to: '/customers', label: 'Customers', icon: '👥', roles: ['admin', 'staff'] },
  { to: '/templates', label: 'Quotation templates', icon: '📝', roles: ['admin', 'staff'] },
  { to: '/products', label: 'Products', icon: '📦', roles: ['admin', 'staff'] },
  { to: '/plans', label: 'Plans', icon: '🗂️', roles: ['admin'] },
  { to: '/taxes', label: 'Taxes', icon: '🧮', roles: ['admin'] },
  { to: '/discounts', label: 'Discounts', icon: '🏷️', roles: ['admin'] },
  { to: '/staff', label: 'Staff', icon: '🛡️', roles: ['admin'] },
  { to: '/portal', label: 'My subscriptions', icon: '🔁', roles: ['customer'], end: true },
  { to: '/portal/invoices', label: 'My invoices', icon: '🧾', roles: ['customer'] },
]
export const navFor = (role) => NAV.filter((n) => n.roles.includes(role))