# UI/UX Design Brief

## Overall Aesthetic
Dark mode. Clean, minimal, premium feel. Inspired by ChatGPT's sidebar layout
combined with Perplexity AI's source card design. Every element has a purpose.
No clutter. Smooth transitions.

## Color Palette
| Role | Hex | Usage |
|---|---|---|
| Background | #0f0f0f | Main page background |
| Surface | #1a1a1a | Sidebar, cards, input area |
| Surface Elevated | #242424 | Message bubbles, hover states |
| Border | #2e2e2e | Dividers, card borders |
| Text Primary | #f0f0f0 | Main text, headings |
| Text Secondary | #8a8a8a | Timestamps, labels, captions |
| Accent | #7c6af7 | Send button, active states, links |
| Accent Hover | #6a58e0 | Button hover |
| Success | #22c55e | High confidence badge |
| Warning | #f59e0b | Medium confidence badge |
| Error | #ef4444 | Low confidence badge, error messages |
| User Bubble | #1e1b4b | User message background |
| AI Card | #1a1a1a | AI response card background |

## Typography
- Primary Font: Inter (Google Fonts CDN)
- Heading Weight: 600
- Body Weight: 400
- Code Font: JetBrains Mono (Google Fonts CDN)
- Base size: 15px
- Line height: 1.7

## Component Style
- Border Radius: 12px for cards, 8px for buttons and inputs, 20px for message bubbles
- Shadows: Subtle only — box-shadow: 0 2px 8px rgba(0,0,0,0.4)
- Primary Button: Accent background (#7c6af7), white text, 8px radius, hover darkens
- Input Field: Surface background, border #2e2e2e, focus border #7c6af7, 12px radius
- Sidebar Item: Hover background #242424, active background #2e2e2e with left accent border

## Response Card Structure
Each AI response is a card containing:
1. Summary section — formatted text with proper paragraph spacing
2. Sources section — horizontal scrollable chips with favicon + domain name
3. Confidence badge — colored pill (✅ High / ⚠️ Medium / ❌ Low)
4. Thin separator between each section

## Typing Indicator
Three animated dots with a label that updates:
- "Searching the web..." (Agent 1)
- "Summarizing results..." (Agent 2)
- "Validating answer..." (Agent 3)
Each stage label fades in/out smoothly.

## Sidebar
- Width: 260px, fixed left
- Top: App logo + name "SearchMind"
- Below logo: "New Chat" button (full width, accent color)
- Below button: scrollable list of past chats
- Each chat item shows: first message truncated to 40 chars + relative timestamp
- Active chat has left border accent

## Dark / Light Mode
Dark mode only in v1. No toggle needed.

## Mobile Responsiveness
- Sidebar collapses on mobile (hamburger menu icon)
- Chat area takes full width on mobile
- Input bar stays fixed at bottom
- Response cards stack vertically and scroll naturally

## Accessibility
- Contrast ratio minimum 4.5:1 for all text
- Input has placeholder text
- Buttons have aria-labels
- Tap targets minimum 44px height