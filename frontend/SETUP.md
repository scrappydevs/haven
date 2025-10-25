# Frontend Setup Instructions

## Quick Start (5 minutes)

### 1. Initialize Next.js App

```bash
cd frontend
npx create-next-app@latest . --typescript --tailwind --app --no-src-dir --import-alias "@/*"
```

When prompted:
- ✅ TypeScript: Yes
- ✅ ESLint: Yes
- ✅ Tailwind CSS: Yes
- ✅ `app/` directory: Yes
- ❌ `src/` directory: No
- ✅ Import alias (@/*): Yes
- ❌ Turbopack: No (optional)

### 2. Install Additional Dependencies

```bash
npm install framer-motion recharts lucide-react
npm install -D @types/node
```

### 3. Install shadcn/ui Components

```bash
npx shadcn-ui@latest init
```

When prompted:
- Style: Default
- Base color: Slate
- CSS variables: Yes

Install key components:
```bash
npx shadcn-ui@latest add button
npx shadcn-ui@latest add card
npx shadcn-ui@latest add badge
npx shadcn-ui@latest add dialog
npx shadcn-ui@latest add toast
```

### 4. Start Development Server

```bash
npm run dev
```

Open http://localhost:3000

---

## Project Structure

After setup, your frontend should look like:

```
frontend/
├── app/
│   ├── page.tsx              # Home page
│   ├── layout.tsx            # Root layout
│   ├── globals.css           # Global styles
│   └── dashboard/            # Dashboard pages (create this)
│       └── page.tsx
├── components/
│   ├── ui/                   # shadcn components (auto-generated)
│   ├── VideoPlayer.tsx       # Create this
│   ├── AlertPanel.tsx        # Create this
│   └── ROICalculator.tsx     # Create this
├── lib/
│   └── utils.ts              # Utility functions
├── public/
│   └── videos/               # Symlink to ../videos/
├── tailwind.config.ts
├── tsconfig.json
└── package.json
```

---

## Environment Variables

Create `.env.local`:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

For production:
```bash
NEXT_PUBLIC_API_URL=https://trialsentinel-api.up.railway.app
```

---

## Key Files to Create

After setup, you'll need to create these components:

### 1. `app/dashboard/page.tsx`
Main dashboard with 6 video feeds

### 2. `components/VideoPlayer.tsx`
Individual video player with CV overlays

### 3. `components/AlertPanel.tsx`
Real-time alerts display

### 4. `components/ROICalculator.tsx`
Cost savings calculator widget

---

## Dark Theme Configuration

Update `tailwind.config.ts`:

```typescript
import type { Config } from "tailwindcss"

const config: Config = {
  darkMode: ["class"],
  content: [
    './pages/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './app/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        // Custom dark theme colors
        background: "hsl(222, 47%, 11%)",  // #0a0e1a
        foreground: "hsl(0, 0%, 100%)",
        card: "hsl(222, 47%, 15%)",
        "card-foreground": "hsl(0, 0%, 100%)",
        primary: {
          DEFAULT: "hsl(217, 91%, 60%)",
          foreground: "hsl(0, 0%, 100%)",
        },
        // ... more colors
      }
    },
  },
  plugins: [require("tailwindcss-animate")],
}
export default config
```

---

## Common Issues

### Issue: Port 3000 already in use
**Solution**:
```bash
kill -9 $(lsof -ti:3000)
# Or use a different port:
npm run dev -- -p 3001
```

### Issue: Module not found
**Solution**:
```bash
rm -rf node_modules package-lock.json
npm install
```

### Issue: Tailwind styles not working
**Solution**: Restart dev server, clear browser cache

---

## Next Steps

1. Run `npm run dev` to start the development server
2. Create the dashboard page (`app/dashboard/page.tsx`)
3. Build video player component
4. Connect to backend API (http://localhost:8000)

See `/docs/FRONTEND_GUIDE.md` for detailed component implementation.
