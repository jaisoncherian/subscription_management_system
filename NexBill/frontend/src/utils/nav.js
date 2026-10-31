export const NAV = [
  {
    group: 'Overview',
    items: [{ to: '/dashboard', label: 'Dashboard', icon: 'dashboard', roles: ['admin', 'staff'] }],
  },
  {
    group: 'Billing',
    items: [
      { to: '/subscriptions', label: 'Subscriptions', icon: 'repeat', roles: ['admin', 'staff'] },
      { to: '/invoices', label: 'Invoices', icon: 'invoice', roles: ['admin', 'staff'] },
      { to: '/payments', label: 'Payments', icon: 'card', roles: ['admin', 'staff'] },
      { to: '/customers', label: 'Customers', icon: 'users', roles: ['admin', 'staff'] },
    ],
  },
  {
    group: 'Catalog',
    items: [
      { to: '/templates', label: 'Quotation templates', icon: 'template', roles: ['admin', 'staff'] },
      { to: '/products', label: 'Products', icon: 'box', roles: ['admin', 'staff'] },
      { to: '/plans', label: 'Plans', icon: 'layers', roles: ['admin'] },
      { to: '/taxes', label: 'Taxes', icon: 'percent', roles: ['admin'] },
      { to: '/discounts', label: 'Discounts', icon: 'tag', roles: ['admin'] },
    ],
  },
  {
    group: 'Team',
    items: [{ to: '/staff', label: 'Staff', icon: 'shield', roles: ['admin'] }],
  },
  {
    group: 'My account',
    items: [
      { to: '/portal', label: 'My subscriptions', icon: 'repeat', roles: ['customer'], end: true },
      { to: '/portal/invoices', label: 'My invoices', icon: 'invoice', roles: ['customer'] },
    ],
  },
]

export const navFor = (role) =>
  NAV.map((section) => ({ ...section, items: section.items.filter((item) => item.roles.includes(role)) }))
    .filter((section) => section.items.length > 0)
