# UI/UX Design Brief

## Overall Aesthetic
Dark mode. Clean, minimal, ultra-premium feel. Inspired by ChatGPT's sidebar layout
combined with Perplexity AI's source card design, enhanced with premium glassmorphism.
Moving background blobs create a floating, lively feel. Every element has a purpose.
No clutter. Smooth transitions.

## Moving Background Blobs
Three large fixed, floating divs with soft radial-gradient colors blur behind the page:
- **Blob 1 (Top-Left)**: Violet-to-transparent gradient (`#8b5cf6`), translates slowly via keyframe floats.
- **Blob 2 (Bottom-Right)**: Purple-to-transparent gradient (`#c084fc`), counter-floats.
- **Blob 3 (Center)**: Indigo-to-transparent gradient (`#4f46e5`).

These create a glowing, dynamic ambiance beneath a semi-transparent surface without impacting text legibility.

## Color Palette
| Role | Hex / Styling | Usage |
|---|---|---|
| Background | #050508 | Deep viewport base background |
| Surface | rgba(10, 10, 16, 0.7) | Sidebar, chat container background |
| Glass Elevate | rgba(255, 255, 255, 0.02) | Message cards, input areas, auth forms |
| Border | rgba(255, 255, 255, 0.06) | Dividers, card glass borders |
| Text Primary | #f3f4f6 | Main headers, prompts, summaries |
| Text Secondary | #9ca3af | Subheadings, dates, domain tags |
| Accent | #8b5cf6 | Glowing buttons, text inputs, active indicators |
| Accent Hover | #a78bfa | Active highlight state |
| Success | #10b981 | High confidence badge border/text |
| Warning | #f59e0b | Medium confidence badge border/text |
| Error / Danger | #ef4444 | Low confidence badge, inline errors |

## Typography
- Primary Font: Inter (Google Fonts CDN)
- Heading Weight: 600
- Body Weight: 400
- Code Font: JetBrains Mono (Google Fonts CDN)
- Base size: 14px
- Line height: 1.7

## Component Style
- Border Radius: 16px/20px for cards and user bubbles, 12px for inputs and buttons.
- Shadows: Soft box-shadows combined with glass borders (`border: 1px solid rgba(255,255,255,0.06)`).
- Main Buttons: Glowing glass button with a linear gradient of violet and transparent border. Hover scales up, shows an internal white glow sweep, and deepens glow shadow.

## Screens

### 1. Premium Authentication Screen
A centered card displaying a glowing logo "S", a minimalist header, and a glassmorphic form card containing:
- Email input
- Password input
- "Sign In" / "Create Account" glowing button
- Smooth state toggle ("Don't have an account? Sign Up")
- Slide/scale entry animations (`animate-scale`) and real-time validation error alerts.

### 2. Main Chat Workspace
Once authenticated, the app displays:
- **Left Sidebar**: Brand brand (glowing "S" + name), quick sign-out button, full-width "New Chat" glass button, vertical scrollable history list with message previews, and the current user's profile email at the bottom.
- **Chat Thread**: Center-aligned stream showing user message bubbles and AI response cards.
- **Input Bar**: A text area with `oninput` auto-resizing, and a glowing send button.

## Response Card Structure
Each AI response is a glass card (`ai-card`) containing:
1. **Summary text** — Formatted paragraphs preserving paragraph line breaks.
2. **Sources row** — Clickable rounded chips with a domain name and favicon image (loaded dynamically from Google Favicon cache).
3. **Confidence badge** — Colored pill reflecting the exact parsed state (✅ High Confidence, ⚠️ Medium Confidence, ❌ Low Confidence).

## Typing Indicator
Bouncing three-dot loader displaying timing-based progress messages:
- *0s - 2.5s*: "🔍 Searching the web..."
- *2.5s - 5s*: "📝 Summarizing results..."
- *5s+*: "✅ Validating answer..."

## Mobile Responsiveness
- Sidebar collapses off-screen left (toggled via a top-left hamburger menu button).
- Input fields and response cards fill viewport width with comfortable padding.
- Text sizes, chips, and layouts wrap automatically.