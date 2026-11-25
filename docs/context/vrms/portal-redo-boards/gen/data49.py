"""Round 49 shared data: people, systems, modules (labels from each system's sidebar), icons, vehicles."""
from parts import LOGO, LOGO_POLY, CHEV, V_VAN, V_L300, V_WING, VAN_TOP, page  # noqa: F401

NAVY, DEEP, GOLD = '#0f1445', '#0a0d33', '#e8b800'
RM = '@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}'


def ic(p, s=18, sw=2, cls=''):
    c = f' class="{cls}"' if cls else ''
    return (f'<svg{c} width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="{sw}" '
            f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{p}</svg>')


I = dict(
    dash='<rect x="3" y="3" width="7" height="9" rx="1"/><rect x="14" y="3" width="7" height="5" rx="1"/><rect x="14" y="12" width="7" height="9" rx="1"/><rect x="3" y="16" width="7" height="5" rx="1"/>',
    cal='<rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18M8 14h2M14 14h2M8 18h2"/>',
    clip='<rect x="8" y="2" width="8" height="4" rx="1"/><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><path d="M12 11h4M12 16h4M8 11h.01M8 16h.01"/>',
    check='<rect x="8" y="2" width="8" height="4" rx="1"/><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><path d="m9 14 2 2 4-4"/>',
    ucheck='<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="m16 11 2 2 4-4"/>',
    truck='<path d="M14 18V6a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2v11a1 1 0 0 0 1 1h2"/><path d="M15 18H9"/><path d="M19 18h2a1 1 0 0 0 1-1v-3.65a1 1 0 0 0-.22-.624l-3.48-4.35A1 1 0 0 0 17.52 8H14"/><circle cx="17" cy="18" r="2"/><circle cx="7" cy="18" r="2"/>',
    wrench='<path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>',
    fuel='<path d="M3 22h12M4 9h10M14 22V4a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v18"/><path d="M14 13h2a2 2 0 0 1 2 2v2a2 2 0 0 0 4 0V9.83a2 2 0 0 0-.59-1.42L18 5"/>',
    plus='<circle cx="12" cy="12" r="10"/><path d="M8 12h8M12 8v8"/>',
    hist='<path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/><path d="M12 7v5l4 2"/>',
    chart='<path d="M3 3v18h18"/><path d="M18 17V9M13 17V5M8 17v-3"/>',
    book='<path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>',
    users='<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/>',
    userx='<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="m17 8 5 5M22 8l-5 5"/>',
    shield='<path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/><path d="m9 12 2 2 4-4"/>',
    idcard='<rect x="2" y="5" width="20" height="14" rx="2"/><circle cx="8" cy="12" r="2"/><path d="M14 10h4M14 14h4"/>',
    key='<circle cx="7.5" cy="15.5" r="5.5"/><path d="m21 2-9.6 9.6M15.5 7.5l3 3L22 7l-3-3"/>',
    garage='<path d="M22 8.35V20a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V8.35A2 2 0 0 1 3.26 6.5l8-3.2a2 2 0 0 1 1.48 0l8 3.2A2 2 0 0 1 22 8.35Z"/><path d="M6 18h12M6 14h12"/><rect x="6" y="10" width="12" height="12"/>',
    coins='<circle cx="12" cy="12" r="10"/><path d="M16 8h-6a2 2 0 1 0 0 4h4a2 2 0 1 1 0 4H8M12 18V6"/>',
    scroll='<path d="M15 12h-5M15 8h-5M19 17V5a2 2 0 0 0-2-2H4"/><path d="M8 21h12a2 2 0 0 0 2-2v-1a1 1 0 0 0-1-1H11a1 1 0 0 0-1 1v1a2 2 0 1 1-4 0V5a2 2 0 1 0-4 0v2a1 1 0 0 0 1 1h3"/>',
    gear='<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>',
    search='<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>',
    pin='<path d="M12 17v5M9 10.76a2 2 0 0 1-1.11 1.79l-1.78.9A2 2 0 0 0 5 15.24V16a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-.76a2 2 0 0 0-1.11-1.79l-1.78-.9A2 2 0 0 1 15 10.76V7a1 1 0 0 1 1-1 2 2 0 0 0 0-4H8a2 2 0 0 0 0 4 1 1 0 0 1 1 1z"/>',
    right='<path d="m9 18 6-6-6-6"/>',
    arrow='<path d="M5 12h14M13 6l6 6-6 6"/>',
    down='<path d="m6 9 6 6 6-6"/>',
    grid='<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/>',
)

# Corazon Villareal (seed): VRMS Chief Mechanic, VMMS Operations, BMS Operations. Module labels from each
# system's sidebar for that role, written in sentence case.
CORAZON = [
    dict(code='BMS', name='Booking Management System', line='Bookings, trips and drivers', role='Operations',
         mods=[('Dashboard', 'dash'), ('Scheduling', 'cal'), ('Job order', 'clip'), ('Vehicle and team availability', 'ucheck')]),
    dict(code='VMMS', name='Vehicle Maintenance Management System', line='Maintenance schedules and fleet upkeep', role='Operations',
         mods=[('Dashboard', 'dash'), ('Fleet vehicles', 'truck'), ('Scheduling', 'cal'), ('Work orders', 'wrench'),
               ('Service logs', 'clip'), ('Fuel management', 'fuel')]),
    dict(code='VRMS', name='Vehicle Repair Management System', line='Repair tickets, mechanics and workshop work', role='Chief Mechanic',
         mods=[('Dashboard', 'dash'), ('Repair tickets', 'wrench'), ('New repair', 'plus'), ('Repair history', 'hist'),
               ('Analytics', 'chart'), ('Knowledge base', 'book')]),
]

# Felicidad Roxas (seed): VMMS Admin and VRMS Admin. Groups follow each sidebar's sections.
FELICIDAD = [
    dict(code='VMMS', name='Vehicle Maintenance Management System', line='Maintenance schedules and fleet upkeep', role='Admin',
         groups=[('Overview', [('Dashboard', 'dash'), ('Analytics', 'chart')]),
                 ('Fleet', [('Fleet vehicles', 'truck'), ('Service garages', 'garage'), ('Outsourced providers', 'garage')]),
                 ('Maintenance', [('Scheduling', 'cal'), ('Work orders', 'wrench'), ('Checklists', 'check'), ('Service logs', 'clip'), ('Reports', 'chart')]),
                 ('Costs', [('Fuel management', 'fuel'), ('Maintenance costing', 'coins')]),
                 ('Admin', [('Audit logs', 'scroll')])]),
    dict(code='VRMS', name='Vehicle Repair Management System', line='Repair tickets, mechanics and workshop work', role='Admin',
         groups=[('General', [('Dashboard', 'dash')]),
                 ('Vehicle repairs', [('Repair tickets', 'wrench'), ('New repair', 'plus'), ('Repair history', 'hist')]),
                 ('Analytics and AI', [('Analytics', 'chart'), ('Knowledge base', 'book')]),
                 ('Administration', [('Users', 'users'), ('Audit logs', 'scroll'), ('Settings', 'gear')])]),
]
for s in FELICIDAD:
    s['mods'] = [m for _, g in s['groups'] for m in g]

# Suite management (portal adminViews.ts). A system admin sees the non suite-only views for their systems;
# counts are sample values.
SUITE_SYS = [('People', 'users', '3 need a look'), ('Deletion requests', 'userx', '1 waiting'), ('Roles', 'idcard', None),
             ('Temporary access', 'key', None), ('Activity', 'hist', None)]
SUITE_ALL = [('Overview', [('Overview', 'dash', None)]),
             ('Accounts', [('People', 'users', '5 need a look'), ('Deletion requests', 'userx', '2 waiting'), ('Suite admins', 'shield', '1 of 3')]),
             ('Access', [('Roles', 'idcard', None), ('Temporary access', 'key', '4 active')]),
             ('Audit', [('Activity', 'hist', None)])]

DATE = 'Wednesday, November 25'

BASE = '''*{box-sizing:border-box}
.pg{width:1440px;min-height:900px;font-family:Inter,system-ui,sans-serif;position:relative;overflow:hidden;color:#0f172a;background:#f3f5f9}
a{color:inherit;text-decoration:none}
.mono{font-family:"IBM Plex Mono",ui-monospace,monospace}
.w{width:1200px;margin:0 auto;position:relative}
.top{position:relative;z-index:3;height:64px;display:flex;align-items:center}
.lk{display:flex;align-items:center;gap:10px}.lk svg{height:20px;fill:#e8b800}.lk span{font-weight:800;font-style:italic;font-size:16px}
.me{margin-left:auto;display:flex;align-items:center;gap:10px;height:44px;padding:0 8px;border-radius:12px;border:0;background:none;color:inherit;font:500 14px Inter,sans-serif;cursor:pointer}
.av{width:34px;height:34px;border-radius:50%;background:rgba(255,255,255,.12);box-shadow:inset 0 0 0 1px rgba(255,255,255,.2);display:grid;place-items:center;font-size:12px;font-weight:600}
.lt .av{background:#e6e9f2;box-shadow:none;color:#0f1445}
.band{position:relative;background:#0f1445;color:#fff;overflow:hidden}
.dt{margin:0;font:600 13px "IBM Plex Mono",monospace;letter-spacing:.04em;color:#e8b800}
'''


def top(name='Corazon Villareal', ini='CV', extra=''):
    return (f'<div class="top"><div class="lk">{LOGO}<span>WeLinc Logistics</span></div>{extra}'
            f'<button class="me" type="button" aria-label="Account menu, {name}"><span class="av">{ini}</span>{name}{CHEV}</button></div>')


def board(title, css, body, logic='renderVals() { return {}; }', h=900):
    return page(title, BASE + css + RM, body, logic=logic, h=h)
