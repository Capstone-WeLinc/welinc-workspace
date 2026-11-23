# Top bar, breadcrumb and sidebar account menu

Status: committed, not yet pushed. Branch `BMS/top-bar-and-breadcrumb` in
`welinc-web-bms` (`c5168dc`), into `development`.

These changes copy the navigation update the VMMS front end (`welinc-web-vmms`,
PR #26, `f3e31ee`) made to its sidebar, breadcrumb and notification bell. BMS
keeps its own colours. Touches only `welinc-web-bms`. No backend change, no
database migrations, and no change to shared auth, portal or the suite
gateway. `welinc-web-vmms` was only read, never changed.

Builds on [0006](../0006-sidebar-and-profile-ui/index.md), which first matched
the BMS sidebar to VMMS.

## 1. New top bar with a breadcrumb

Files: `src/components/Navbar.tsx` (new), `src/components/Sidebar.tsx`

### What it does
- A white bar, 64px high, sits across the top of every signed-in page. It
  stays in place while the page scrolls.
- On the left, a **breadcrumb** shows where you are, written as
  *group › page*:
  - Pages inside a sidebar section show the section name, for example
    *Booking Management › Scheduling* or *Administration › Approvals*.
  - Pages outside a section show *BMS*, for example *BMS › Dashboard*. Every
    Operations and Customer Service page is shown this way, since those menus
    have no sections.
  - Each role's profile page shows *Account › Profile*.
  - A page that isn't in the menu gets its name from the last part of its
    address, for example `/admin/settings` shows *BMS › Settings*.
- On the right is the notification bell (section 2).
- The page content sits under the bar and keeps its 24px padding.

The breadcrumb reads the same menu as the sidebar (`getNavItems(role)`), so a
new menu entry shows up in the breadcrumb on its own.

## 2. Notification bell moves to the top bar

File: `src/components/shared/NotificationBell.tsx`

### What it does
- The bell now sits at the right end of the top bar instead of in the sidebar
  footer.
- It is a 40px square button with a light border, like VMMS. The unread count
  sits on its top-right corner and still shows `99+` past 99.
- The badge keeps the BMS gold `#d4a72c`.

### Unchanged
- The notification panel: it still opens centred over the page (0006), with
  the same content, **Mark all read** and **View all**.
- How notifications are fetched, stored and shown as toasts.

### Removed
- The bell and its "Notifications" label in the sidebar footer.

## 3. Sidebar: account menu and flatter style

File: `src/components/Sidebar.tsx`

### What it does
- **Account menu:** the footer now shows only your avatar, name and role.
  Clicking it opens a small menu **above** it with your name and email,
  **Profile** and **Sign out**. Clicking outside the menu, pressing Esc or
  changing page closes it. The menu is drawn on `<body>` so the sidebar can't
  clip it.
- **Back to home:** "Switch system" is renamed **Back to home**, with a house
  icon. It still shows to the same people and still opens the portal launcher
  with BMS marked (`switchSystemUrl()`, BMS spec 0007 rules). VMMS hides it
  for its Operations role and links to the portal's home page; BMS kept its
  own rule.
- **Flatter style**, as in VMMS:
  - no shadow on the sidebar, the logo frame, the active link or the
    active-section dot
  - links and section headings use slightly less rounded corners
  - the active link and section headings use a lighter font weight
  - keyboard focus shows a clearer ring
  - the avatar is now a circle

### Unchanged
- The colours: navy `#020849`, the yellow `#f4c400` active link, `#9ba4db`
  text and red sign out. The VMMS colour change was left out on purpose.
- The menu entries, sections and who sees them (`getNavItems(role)`).
- Sign out still signs out straight away, with no confirm step.

### Removed
- The separate Profile and Sign Out buttons in the sidebar footer. Both are in
  the account menu now.

## 4. Less empty space above page content

### Page header
File: `src/components/pageheader/Pageheader.tsx`

The default page header spacing had 40px of top padding on top of the page's
own 24px. With the new top bar, this left the icon, title and subtitle too low.
The 40px top padding is removed. The side and bottom padding stay. This affects
every page that uses the default header spacing.

### Tabs under the header
Files: `src/pages/admin/CrewManagement.tsx` (Drivers / Helpers),
`src/pages/admin/ActivityLogs.tsx` (BMS work / Accounts)

The tab bars sat 52px below the header: the header's 32px bottom margin plus
the tab bar's own 20px top margin. The tab bar is an inline element, so the two
margins add up instead of overlapping. The tab bar's top margin is removed on
these two pages, so the gap is now 32px, the same as on other pages.

## Testing

- The web app type-checks (`npm run typecheck`) and the changed files lint
  clean.
- Unit tests pass (`npm test`, 20 tests).
- The running app at `http://localhost:8003` serves the new code after a
  container restart. Not yet checked by hand on every page and role.

## Local dev note

On Windows, file changes don't always reach the Docker `web-bms` container
(see 0006). If an edit doesn't show, run `docker restart welinc_bms_frontend`,
then hard-refresh (Ctrl + Shift + R). BMS runs on port 8003.

## Deploy notes

- No backend or database changes, so it can merge on its own.
- Merging into `development` triggers the staging deploy.
