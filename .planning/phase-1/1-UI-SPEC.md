# UI-SPEC: Task Gantt Chart — Design Contract

**Phase:** Phase 1 (UI/UX Polish)

**Version:** 1.0

**Status:** Draft

---

## Design System

### Color Palette

```
Primary:     #2563EB (Blue)
Secondary:   #7C3AED (Purple)
Accent:      #EC4899 (Pink)

Success:     #10B981 (Green)
Warning:     #F59E0B (Amber)
Error:       #EF4444 (Red)
Info:        #3B82F6 (Info Blue)

Dark:        #1F2937 (Gray-800)
Text:        #374151 (Gray-700)
Border:      #E5E7EB (Gray-200)
Surface:     #F9FAFB (Gray-50)
Background:  #FFFFFF (White)

Chart Bar:   #3B82F6 (Task blue)
Arrow:       #FF9800 (Orange)
Weekend:     #F9FAFB (Gray-50) @ 50% opacity
Grid:        #E5E7EB (Gray-200)
```

**Accessibility:**
- All text/background combos must meet WCAG AA (4.5:1 ratio)
- Warning/Error only not to be color-only (include icon or text indicator)

### Typography

```
Font Family (all): 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif
Monospace:         'Monaco', 'Courier New', monospace

H1: 32px, weight 700, line-height 1.2
H2: 24px, weight 600, line-height 1.2
H3: 20px, weight 600, line-height 1.2

Body:   16px, weight 400, line-height 1.5
Small:  14px, weight 400, line-height 1.5
Tiny:   12px, weight 400, line-height 1.4

Button: 16px, weight 600, uppercase

Gantt:  12px (labels), 11px (axis), mono for dates
```

**Hierarchy:**
- H1: Page titles (Login, Projects, Gantt)
- H2: Section headers (Task list, Project info)
- H3: Subsections (Filters, Settings)
- Body: Primary content, form labels
- Small: Helper text, timestamps
- Tiny: Secondary annotations, chart labels

### Spacing Scale

```
0:  0px
1:  4px
2:  8px
3:  12px
4:  16px
5:  20px
6:  24px
8:  32px
10: 40px
12: 48px
16: 64px
```

**Common Patterns:**
- Button padding: 8px 16px (vertical, horizontal)
- Input padding: 12px 16px
- Card padding: 24px
- Section margin: 32px
- Gap (flex): 16px
- Border-radius (small): 4px
- Border-radius (button): 6px
- Border-radius (card): 8px

### Shadows

```
Small:  0 1px 2px rgba(0,0,0,0.05)
Medium: 0 4px 6px rgba(0,0,0,0.1)
Large:  0 10px 15px rgba(0,0,0,0.1)

Hover:  Medium
Active: Large
```

---

## Component Specs

### 1. Login Form

**Layout:** Centered card, max-width 400px

**Components:**
- H1: "Login" (center, margin-bottom: 32px)
- Label "Username" → Input[type=text] (width 100%, 40px height)
  - Placeholder: "Enter username"
  - Margin-bottom: 16px
- Label "Password" → Input[type=password] (width 100%, 40px height)
  - Placeholder: "Enter password"
  - Margin-bottom: 24px
- Button "Login" (primary, width 100%, 44px height)
- Link "Demo user: demo / Demo@1234" (small, margin-top 16px, gray text)

**States:**
- Default: All fields empty, button enabled
- Filled: Button highlights on hover
- Error: Red border on input, error text below (12px, red)
- Loading: Button shows spinner, disabled

**Responsive:**
- Mobile: Full-width card with 16px padding
- Desktop: Max-width 400px, centered

---

### 2. Project List

**Layout:** Sidebar (left) + Main content (right)

**Sidebar (Left panel, 250px):**
- H2: "Projects" (20px, margin-bottom: 16px)
- Project cards (white bg, border 1px gray, margin-bottom: 8px):
  - Project name (16px, weight 600)
  - Hover: Light gray bg, cursor pointer
  - Active: Blue left border (4px), blue text
- Button "New Project" (secondary, width 100%, margin-top: 16px)

**Main content (Right panel, flex 1):**
- H1: "{Project Name}" (32px, margin-bottom: 8px)
- Description (small, gray text, margin-bottom: 24px)
- "Tasks: X" (12px, gray)
- Task list below

**Responsive:**
- Mobile: Stack vertically (projects above, content below)
- Tablet: Side-by-side with smaller sidebar (180px)
- Desktop: Side-by-side (250px sidebar)

---

### 3. Task Creation Form

**Layout:** Floating card or modal, max-width 500px

**Components:**
- H2: "Add Task" (24px, margin-bottom: 16px)
- Label "Task Name" → Input[type=text]
  - Placeholder: "e.g., Design mockups"
  - Margin-bottom: 16px
- Label "Start Date" → Input[type=date]
  - Margin-bottom: 16px
- Label "End Date" → Input[type=date]
  - Margin-bottom: 16px
- Label "Dependent On (optional)" → Select
  - Options: "None" (default), list of tasks
  - Margin-bottom: 24px
- Buttons (flex, gap 8px):
  - "Add" (primary)
  - "Cancel" (secondary)

**Validation:**
- Required fields marked with * (red)
- Inline error below field (12px, red)
- End date >= start date (validated on blur)
- Task name max 100 chars

**States:**
- Default: Empty, "Add" button enabled
- Filled: Button highlights
- Error: Red borders, error text
- Loading: Buttons disabled, spinner on "Add"
- Success: Form clears, toast appears

---

### 4. Task List

**Layout:** Vertical list, each task is a card

**Card Structure (white bg, border 1px gray, padding 16px, margin-bottom 8px):**
- Row 1: Task name (16px, weight 600) | Delete button (small, gray)
- Row 2: Date range (12px, gray) "YYYY-MM-DD → YYYY-MM-DD"

**States:**
- Default: Light gray bg on hover
- Dragging: Blue outline, opacity 80%
- Active (selected on chart): Blue left border (4px)

**Responsive:**
- Desktop: Full width list
- Mobile: Stacked, full width

---

### 5. Gantt Chart

**Container:**
- White background
- Border-top 1px gray
- Padding: 20px
- Scrollable horizontally for long timelines

**Layout:**
- Left axis: Task names (150px wide, right-aligned, -10px x-offset)
  - 12px mono font
  - Truncate if >25 chars, full name on hover
- Center: Chart area
  - X-axis: Dates (weekly ticks, "May 15", "May 22", etc.)
  - Y-axis: Task rows (50px height each)
  - Grid lines: Vertical (weekly dashed, 1px gray)
  - Light grid lines: Daily (very light, 0.5px)

**Task Bars:**
- SVG `<rect>` elements
- Height: 24px (within 50px row)
- Background: #3B82F6 (blue)
- Border-radius: 4px
- Min width: 100px (expand if task >1 day)
- Text label on bar:
  - 12px white text, semibold
  - Smart truncation (measure bar width, estimate chars)
  - Only show if bar width >80px
  - Padding: 5px left/right
  - Full name on hover (title attribute)

**Dependency Arrows:**
- SVG `<path>` elements
- Stroke: #FF9800 (orange), 2px
- Curved (Quadratic Bezier): Start (end of dep task) → End (start of dependent)
- Arrowhead: Orange triangle (10x10px)
- Opacity: 100% default, 60% on hover of non-related arrows

**Weekend Blocks:**
- SVG `<rect>` behind all content
- Fill: #F9FAFB (gray) @ 50% opacity
- Height: Full chart height
- Saturday-Sunday only

**Cursor States:**
- Over empty area: Default
- Over task bar: "grab" (open hand)
- While dragging: "grabbing" (closed hand)

**Responsive:**
- Desktop (1024px+): Full interactive Gantt
- Tablet (768px+): Horizontal scroll, touch-friendly targets
- Mobile (<768px): Simplified view (timeline only, no drag)

---

### 6. Buttons

**Primary (CTA):**
- Background: #2563EB (blue)
- Text: White
- Height: 44px (accessibility minimum)
- Padding: 8px 16px
- Border-radius: 6px
- Font: 14px, weight 600, uppercase
- Hover: Darken to #1D4ED8
- Active: Even darker, box-shadow: inset
- Disabled: Gray background, opacity 50%, cursor: not-allowed

**Secondary:**
- Background: #F3F4F6 (gray-100)
- Text: #374151 (gray-700)
- Same dimensions as primary
- Hover: Darken to #E5E7EB
- Active: #D1D5DB

**Ghost:**
- Background: Transparent
- Text: #2563EB (blue)
- Border: 1px solid #2563EB
- Hover: Light blue background
- Active: Darker blue

**Danger:**
- Background: #EF4444 (red)
- Text: White
- Same dimensions
- Hover: Darken to #DC2626
- Active: Even darker

---

### 7. Form Inputs & Select

**Text Input / Textarea:**
- Height: 40px (input), min-height 80px (textarea)
- Padding: 12px 16px
- Border: 1px solid #E5E7EB
- Border-radius: 6px
- Font: 14px, #374151
- Background: White
- Placeholder: Gray (#9CA3AF)

**States:**
- Default: Gray border
- Focus: Blue border (2px), box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1)
- Hover: Slightly darker border
- Disabled: Gray bg (#F9FAFB), opacity 50%
- Error: Red border (2px), error text below (12px, red)

**Label:**
- 14px, weight 600, #374151
- Margin-bottom: 8px
- Required fields: Red * after text

**Select:**
- Same as input
- Dropdown arrow (right side, 12px)
- Options: 14px text, padding 8px 16px
- Hover option: Light blue bg
- Selected: Blue bg, white text

**Date Input:**
- Same as text input
- Browser native date picker
- Format: YYYY-MM-DD

---

### 8. Notifications / Toasts

**Success Toast:**
- Background: #10B981 (green)
- Text: White
- Icon: ✓ (checkmark)
- Position: Bottom-right, 16px margin
- Duration: 3 seconds auto-dismiss
- Padding: 16px

**Error Toast:**
- Background: #EF4444 (red)
- Text: White
- Icon: ✗ (x)
- Position: Bottom-right, 16px margin
- Duration: 5 seconds (manual dismiss option)
- Padding: 16px

**Info Toast:**
- Background: #3B82F6 (blue)
- Text: White
- Icon: ⓘ (info)
- Position: Bottom-right
- Duration: 3 seconds

---

### 9. Empty States

**No projects:**
- Icon: 📋 (or SVG)
- Headline: "No projects yet"
- Subtext: "Create your first project to get started"
- Button: "New Project"
- Centered on screen

**No tasks:**
- Icon: ✓ (or SVG)
- Headline: "No tasks yet"
- Subtext: "Add a task to see your timeline"
- Button: "Add Task"
- Centered on chart area

---

## Responsive Design Grid

```
Mobile    (320px - 767px):  1 column
Tablet    (768px - 1023px): 2 columns  
Desktop   (1024px+):        3+ columns
```

**Breakpoint Rules:**
- Mobile: Stack all elements vertically, touch-friendly (44px minimum buttons)
- Tablet: 2-column layout, sidebar collapses to icon-only
- Desktop: Full layout with all details visible

---

## Interaction Specs

### Drag-to-Move (Horizontal)

**Trigger:** `mousedown` on task bar

**Behavior:**
1. Bar gets "dragging" class (blue outline)
2. Cursor changes to "grabbing"
3. On `mousemove`: Calculate deltaX
4. Calculate `daysShifted = Math.round(deltaX / dayWidth)`
5. Update task dates (both start and end)
6. On `mouseup`: Send API request, re-render chart

**Visual Feedback:**
- Cursor: grab → grabbing
- Opacity: 100% → 80% (dragging)
- Preview: Optional (show date preview while dragging)

**Edge Cases:**
- Drag <5px: Ignored (no update)
- Drag past max date: Clamp to max date
- Drag on locked tasks: Disabled (future phase)

### Swimlane Reorder (Vertical)

**Trigger:** `mousedown` on task bar + vertical drag >threshold

**Behavior:**
1. Detect vertical movement (deltaY)
2. Calculate `rowsShifted = Math.round(deltaY / taskHeight)`
3. Reorder tasks array
4. Re-render chart with new order
5. No database update (local reordering only, persists via localStorage)

**Visual Feedback:**
- Ghost/preview of new position
- Tasks swap positions smoothly

---

## Keyboard Navigation

| Key | Action |
|-----|--------|
| `Tab` | Focus next element |
| `Shift+Tab` | Focus previous element |
| `Enter` | Activate button, submit form |
| `Escape` | Close modal, cancel action |
| `↑` / `↓` | Navigate task list |
| `←` / `→` | Shift task date by 1 day |
| `Ctrl+N` | New task |
| `Ctrl+S` | Save/Submit |
| `Del` | Delete selected task |

---

## Accessibility Standards

**Target: WCAG 2.1 AA**

- ✓ Color contrast: 4.5:1 minimum (text)
- ✓ Keyboard accessible: All features usable via keyboard
- ✓ Screen reader friendly: Proper headings, ARIA labels
- ✓ Focus visible: Blue outline on focused elements
- ✓ Error messages: Associated with form fields
- ✓ Readable fonts: Sans-serif, 16px minimum

---

## File Structure

```
index.html
├── <head>
│   └── <style> (CSS inline)
├── <body>
│   ├── .login-screen (display: none hidden)
│   │   ├── .login-card
│   │   │   ├── h1
│   │   │   ├── form
│   │   │   │   ├── input#username
│   │   │   │   ├── input#password
│   │   │   │   └── button (type submit)
│   │   │   └── .demo-hint
│   │   └── .auth-container
│   ├── .main-screen (display: flex hidden)
│   │   ├── .sidebar
│   │   │   ├── h2
│   │   │   ├── #projectsList
│   │   │   └── button (new project)
│   │   ├── .main-content
│   │   │   ├── #chartTitle
│   │   │   ├── #projectInfo
│   │   │   ├── .task-form
│   │   │   │   ├── inputs (task name, dates, dependency select)
│   │   │   │   └── button (add task)
│   │   │   ├── #tasksList
│   │   │   └── #gantt-container (D3 chart goes here)
│   └── <script> (JavaScript inline)
```

---

## Performance Targets

| Metric | Target |
|--------|--------|
| Page load | <2s |
| Gantt render (10 tasks) | <200ms |
| Gantt render (100 tasks) | <500ms |
| Drag frame rate | 60fps |
| API response | <100ms |
| Asset size | <200KB total |

---

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+
- Mobile Safari 14+ (iOS)
- Chrome Mobile 90+ (Android)

**Not supported:**
- IE11 (end of life)
- Old Android browsers (<5.0)

---

## Design Tokens (CSS Variables)

```css
:root {
  /* Colors */
  --color-primary: #2563EB;
  --color-secondary: #7C3AED;
  --color-accent: #EC4899;
  --color-success: #10B981;
  --color-warning: #F59E0B;
  --color-error: #EF4444;
  --color-info: #3B82F6;
  
  --color-dark: #1F2937;
  --color-text: #374151;
  --color-border: #E5E7EB;
  --color-surface: #F9FAFB;
  --color-bg: #FFFFFF;
  
  /* Typography */
  --font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  --font-mono: 'Monaco', 'Courier New', monospace;
  --font-size-h1: 32px;
  --font-size-h2: 24px;
  --font-size-body: 16px;
  --line-height-body: 1.5;
  
  /* Spacing */
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-6: 24px;
  --space-8: 32px;
  
  /* Shadows */
  --shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
  --shadow-md: 0 4px 6px rgba(0,0,0,0.1);
  
  /* Radius */
  --radius-sm: 4px;
  --radius-md: 6px;
  --radius-lg: 8px;
}
```

---

**UI-SPEC Status:** Draft

Last updated: 2026-05-08
