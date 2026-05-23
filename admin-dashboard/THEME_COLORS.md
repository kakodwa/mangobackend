# Mango Marketplace Admin Dashboard - Color Theme

## Brand Colors (from Flutter App)

This admin dashboard uses the exact color palette from the Mango Marketplace Flutter application for consistency across all platforms.

### Primary Colors

| Color Name | Hex Code | RGB | Usage |
|-----------|----------|-----|-------|
| **Mango Orange** | `#FF8C00` | rgb(255, 140, 0) | Primary brand color, buttons, links, highlights |
| **Mango Light** | `#FFA726` | rgb(255, 167, 38) | Secondary highlights, hover states, gradients |
| **Leaf Green** | `#2E7D32` | rgb(46, 125, 50) | Success states, approved items, positive actions |
| **Dark Text** | `#212121` | rgb(33, 33, 33) | Primary text, headings, dark content |

### Extended Palette

| Color Name | Hex Code | Usage |
|-----------|----------|-------|
| **Primary Dark** | `#E07B00` | Darker states of primary button on hover/active |
| **Secondary Dark** | `#E89200` | Darker states of secondary elements |
| **Accent Dark** | `#1B5E20` | Darker green for accent elements |
| **Danger** | `#D32F2F` | Error messages, delete actions, alerts |
| **Warning** | `#F57C00` | Warning messages, pending actions |
| **Info** | `#0288D1` | Information messages, neutral alerts |

### Neutral Colors

| Color Name | Hex Code | Usage |
|-----------|----------|-------|
| **Background** | `#FAFAFA` | Page background, secondary surfaces |
| **Surface** | `#FFFFFF` | Cards, panels, modals, primary surfaces |
| **Border** | `#E0E0E0` | Dividers, borders, subtle separators |
| **Text Primary** | `#212121` | Main text content |
| **Text Secondary** | `#757575` | Secondary text, subtitles, labels |
| **Text Light** | `#BDBDBD` | Placeholder text, disabled states |

## Color Usage Guidelines

### For Buttons

- **Primary Button**: Mango Orange background with white text
- **Secondary Button**: Mango Light background with white text
- **Success Button**: Leaf Green background with white text
- **Danger Button**: Danger red background with white text
- **Disabled Button**: Gray background with light gray text

### For Status Badges

- **Approved/Active**: Leaf Green background with white text
- **Pending/Warning**: Warning orange background with white text
- **Rejected/Error**: Danger red background with white text
- **Draft**: Gray background with dark text

### For Alerts & Messages

- **Success Alert**: Leaf Green border with light green background
- **Warning Alert**: Warning orange border with light orange background
- **Error Alert**: Danger red border with light red background
- **Info Alert**: Blue border with light blue background

### For Gradients

The dashboard uses the following gradient combinations:

```css
/* Hero/Hero section gradient */
linear-gradient(135deg, #FF8C00 0%, #FFA726 100%)

/* Sidebar logo gradient */
linear-gradient(135deg, #FF8C00 0%, #FFA726 100%)

/* Feature cards accent */
linear-gradient(135deg, #FF8C00 0%, #2E7D32 100%)
```

## Accessibility Notes

- **Contrast Ratio for Text**: All primary text uses #212121 (darkText) which provides excellent contrast on light backgrounds (WCAG AAA)
- **Focus States**: All interactive elements use the primary Mango Orange color for focus states
- **Colorblind Safe**: The palette includes sufficient luminosity differences to be accessible to colorblind users
- **Disabled States**: Disabled elements use reduced opacity (50-60%) rather than color changes alone

## Implementation in Code

### CSS Variables (in `css/styles.css`)

```css
:root {
  --primary: #FF8C00;           /* mangoOrange */
  --primary-dark: #E07B00;      /* Darker mango orange */
  --secondary: #FFA726;         /* mangoLight */
  --secondary-dark: #E89200;    /* Darker mango light */
  --accent: #2E7D32;            /* leafGreen */
  --accent-dark: #1B5E20;       /* Darker leaf green */
  --success: #2E7D32;           /* leafGreen for success */
  --danger: #D32F2F;            /* Deep red for danger */
  --warning: #F57C00;           /* Orange warning */
  --info: #0288D1;              /* Blue info */
  
  --text-primary: #212121;      /* darkText from Flutter */
  --text-secondary: #757575;
  --text-light: #BDBDBD;
  
  --background: #FAFAFA;
  --surface: #FFFFFF;
  --border: #E0E0E0;
}
```

### Using CSS Variables in Components

```css
/* Button */
.btn-primary {
  background-color: var(--primary);
  color: white;
}

.btn-primary:hover {
  background-color: var(--primary-dark);
}

/* Text */
.text-primary {
  color: var(--primary);
}

/* Background */
.bg-success {
  background-color: var(--success);
}
```

## Flutter App Color Mapping

This admin dashboard color system maps directly to the Flutter app's `AppColors` class:

```dart
// Flutter App
static const Color mangoOrange = Color(0xFFFF8C00);    // --primary
static const Color mangoLight = Color(0xFFFFA726);     // --secondary
static const Color leafGreen = Color(0xFF2E7D32);      // --accent / --success
static const Color darkText = Color(0xFF212121);       // --text-primary
```

## Customization

To change the theme colors globally, update the CSS variables in `/admin-dashboard/css/styles.css` in the `:root` selector. All elements will automatically update since they use CSS variables throughout.

### Example: Change Primary Color

```css
:root {
  --primary: #YOUR_NEW_COLOR;
  --primary-dark: #YOUR_NEW_DARK_COLOR;
}
```

All buttons, links, and primary elements will update immediately.

## Color Palette Preview

```
███████ #FF8C00 - Mango Orange (Primary)
███████ #FFA726 - Mango Light (Secondary)
███████ #2E7D32 - Leaf Green (Accent)
███████ #212121 - Dark Text (Text Primary)
███████ #FFFFFF - White (Surface)
███████ #FAFAFA - Light Gray (Background)
```

## Version History

- **v1.0** (2024) - Initial theme based on Flutter app colors
  - Primary: Mango Orange (#FF8C00)
  - Secondary: Mango Light (#FFA726)
  - Accent: Leaf Green (#2E7D32)
  - Text: Dark (#212121)
