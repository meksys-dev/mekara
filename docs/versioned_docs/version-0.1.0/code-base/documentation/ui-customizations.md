---
sidebar_position: 2
---

# UI Customizations

The Mek documentation site includes several custom UI elements and styling to evoke a futuristic feel.

## Color Scheme

The site uses a custom color palette defined in `custom.css` with different colors for the default dark mode and an unused light mode.

### Dark Mode (Default)

- Primary color: Cyan (`#bff7f9`)
- Dark background: Near black (`#090b0d`)
- Highlighted code blocks use cyan with transparency
- Sidebar hover and active backgrounds share a dedicated cyan-tinted overlay (`--ifm-menu-color-background-hover` and `--ifm-menu-color-background-active`)

### Light Mode

- Default Docusaurus shades of green

## Custom Fonts

The site uses two custom font families stored in `docs/static/fonts/private/` (a private submodule).

### Conditional Loading

Font definitions live in `src/css/fonts.css`, separate from the main `src/css/custom.css`. The `docusaurus.config.ts` checks at build time whether an actual font file exists (not just the directory, since empty submodule checkouts create the directory). Two mechanisms work together:

1. **Conditional CSS inclusion**: `fonts.css` is only added to `customCss` when fonts are present
2. **Webpack IgnorePlugin**: A custom plugin ignores `fonts.css` imports when fonts are missing, preventing Webpack from scanning it

This allows CI and contributors without access to the private fonts to build the site successfully—headings and sidebar text will fall back to system sans-serif fonts.

### Font Families

### Nasalization

Used for headings and interactive elements (buttons):

- Article h1 headings (small-caps, uppercase)
- Navbar site title (uppercase)
- Navbar "Docs" link (small-caps)
- Hero banner buttons

Available weights:

- 200 (Light)
- 400 (Regular)
- 700 (Bold)
- 900 (Heavy)

Each weight is available in both normal and italic styles.

### Good Timing

Used for:

- Body text and descriptive paragraphs in the hero banner
- All sidebar navigation menu items
- Article headings (h2 through h6)

Available weights:

- 200 (Extra Light)
- 300 (Light)
- 400 (Regular)
- 500 (Medium)
- 600 (Semi-Bold)
- 700 (Bold)
- 900 (Heavy)

Each weight is available in both normal and italic styles.

## Hero Banner

The homepage hero banner features custom styling with the following elements:

### Layout

- Minimum height of 800px
- Centered content with title, tagline, and action button
- Background image (`mekara-full-size.png`) displayed at center with contain sizing

### Text Styling

- **Title (h1)**: Uses Nasalization font, uppercase, 80px size, 300 weight
  - Cyan text shadow with multi-layer glow effect (`0 0 7px`, `0 0 10px`, `0 0 21px`)
- **Tagline (p)**: Uses Good Timing font with cyan glow text shadow
- **Background**: Semi-transparent dark background with 10px blur effect

### Animations

The hero banner includes entry animations that play on page load:

- **Banner expansion**: The content container starts collapsed (`scaleY(0)`) and invisible, then expands vertically to full height over 0.8s with a 0.3s initial delay. Uses a cubic-bezier easing (`0.16, 1, 0.3, 1`) for a smooth, slightly accelerated expansion.
- **Button fade-in**: The call-to-action button fades in over 0.5s, starting after an 0.8s delay so it appears as the banner finishes expanding.

### Interactive Elements

- Buttons use Nasalization font with uppercase text
- Cyan border with matching text color
- Hover effect adds a glowing shadow effect with smooth 0.3s transition
- Shadow grows to `0 0 5px`, `0 0 10px`, `0 0 20px` on hover for interactive feedback

## Navigation and Sidebar Styling

Active navigation and sidebar items display a cyan glow effect to indicate the current page, maintaining consistency with the overall cyberpunk aesthetic.

### Active Navbar Links

- Uses `.navbar__link--active` selector
- Applies cyan text shadow with multi-layer glow: `0 0 2px`, `0 0 3px`, `0 0 5px`
- Color: `var(--glow-cyan)` (CSS variable for `#4d99b3`)

### Sidebar Links

##### Requirements

- All menu items in the path to the active page (e.g., `Development > Quickstart > For AIs`) render in the cyan link color to show hierarchy context
- Only the active leaf item:
  - Gets the cyan-tinted glow around its text (the same glow color as on the hero banner)
  - Has a cyan-colored background with a left-side corner rounding

### Implementation

- Active-state selector scopes both collapsible headers and leaf links: `.menu__list-item-collapsible--active .menu__link--active, .menu__list-item > a.menu__link--active`
- Glow effect matches navbar links with cyan text shadows: `0 0 2px`, `0 0 3px`, `0 0 5px`
- Background tint comes from `--ifm-menu-color-background-active` and hover tint from `--ifm-menu-color-background-hover`; both are set to the same value.
- Border radius is applied as (4px 0 0 4px) to give the active item a pill-like leading edge while remaining flush with the sidebar's right edge

### Glow Color Variable

The glow color is defined as a CSS variable `--glow-cyan: #4d99b3` in the dark theme configuration (`custom.css`). This variable is used throughout the site for all glowing effects on:

- Hero banner text and buttons
- Active navigation links
- Active sidebar links

## Configuration

### Docusaurus Settings (`docusaurus.config.ts`)

- Theme: Set to dark mode by default (`defaultMode: 'dark'`)
- Theme switcher: Disabled (`disableSwitch: true`)
- Respect system preferences: Disabled (`respectPrefersColorScheme: false`)
- Site title: "Mekara"
- Production URL: `https://docs.meksys.dev`

### Responsive Design

The hero banner includes a media query for screens narrower than 996px that adjusts padding from 4rem to 2rem to accommodate smaller viewports.

## Visual Identity

The UI customizations create a cohesive visual identity with:

- **Cyberpunk aesthetic**: Cyan glowing text effects on dark background
- **Mecha-inspired branding**: Custom fonts that complement the "mecha-grade automation" tagline
- **Accessibility**: High contrast cyan-on-dark color scheme maintains readability
- **Consistency**: Unified use of custom fonts and color palette throughout the hero section
