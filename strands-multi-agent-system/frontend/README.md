# 🚀 Golden Config AI - Enterprise Frontend

Modern, enterprise-grade web application for configuration drift analysis built with React, TypeScript, and Tailwind CSS.

## 📦 Tech Stack

- **React 18** - Modern component architecture
- **TypeScript 5** - Type-safe development
- **Vite 5** - Lightning-fast build tool with HMR
- **Tailwind CSS 3** - Utility-first CSS framework
- **Shadcn/ui** - Beautiful, accessible component library
- **TanStack Query** - Powerful data fetching and caching
- **React Router v6** - Client-side routing
- **Zustand** - Simple state management
- **Lucide React** - Modern icon library
- **Sonner** - Toast notifications

## 🏗️ Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── ui/              # Shadcn UI components
│   │   ├── layout/          # Layout components (Header, Layout)
│   │   ├── dashboard/       # Dashboard components (ServiceCard, StatCard, DriftItem)
│   │   └── common/          # Shared components
│   ├── pages/
│   │   ├── Overview.tsx     # Services overview page
│   │   └── ServiceDetail.tsx # Service detail with drift analysis
│   ├── hooks/
│   │   ├── useServices.ts   # Services data hooks
│   │   └── useLLMOutput.ts  # LLM output data hooks
│   ├── lib/
│   │   ├── api.ts           # API client (Axios)
│   │   └── utils.ts         # Utility functions
│   ├── types/
│   │   ├── service.ts       # Service type definitions
│   │   └── drift.ts         # Drift type definitions
│   ├── App.tsx              # Main app component
│   ├── main.tsx             # Entry point
│   └── index.css            # Global styles (Tailwind)
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.js
└── postcss.config.js
```

## 🚀 Getting Started

### Prerequisites

- Node.js 18+ and npm
- FastAPI backend running on http://localhost:3000

### Installation

```bash
cd frontend
npm install
```

### Development

Run the development server with hot module replacement:

```bash
npm run dev
```

The app will be available at http://localhost:5173

**Note:** The Vite dev server proxies `/api` requests to http://localhost:3000 (FastAPI backend).

### Build for Production

Build the app for production:

```bash
npm run build
```

This will:
1. Compile TypeScript
2. Bundle with Vite
3. Output to `../api/static/` (served by FastAPI)

### Preview Production Build

```bash
npm run preview
```

## 🎨 Features

### ✅ **Services Overview**
- View all configured services at a glance
- See environment badges (Production, QA, Dev)
- Quick access to run analysis
- Navigate to detailed view

### ✅ **Service Detail Dashboard**
- Comprehensive summary statistics
- Tabbed view by risk level (High, Medium, Low, Allowed)
- AI-generated insights for each drift
- Side-by-side diff comparison
- Remediation suggestions

### ✅ **AI Review Assistant**
- Potential risk analysis
- Suggested actions
- Environment-aware recommendations

### ✅ **Modern UX**
- Responsive design (mobile, tablet, desktop)
- Loading skeletons
- Toast notifications
- Error handling
- Real-time data fetching

## 🔧 Configuration

### Environment Variables

Create `.env` in the frontend directory (optional):

```env
VITE_API_URL=http://localhost:3000
```

### API Proxy (Development)

The `vite.config.ts` configures a proxy for API requests:

```typescript
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:3000',
      changeOrigin: true,
    },
  },
}
```

## 📊 API Integration

The frontend communicates with the FastAPI backend via these endpoints:

- `GET /api/services` - List all services
- `POST /api/services/{id}/analyze` - Run analysis
- `GET /api/services/{id}/llm-output` - Get drift analysis results

## 🎨 Customization

### Adding New Components

Use Shadcn CLI to add new components:

```bash
npx shadcn-ui@latest add [component-name]
```

Available components: button, card, dialog, dropdown-menu, tabs, etc.

### Styling

Tailwind CSS utility classes are used throughout. To customize:

1. Edit `tailwind.config.js` for theme customization
2. Edit `src/index.css` for global CSS variables

### Adding New Pages

1. Create a new component in `src/pages/`
2. Add route in `src/App.tsx`
3. Update navigation in `src/components/layout/Header.tsx`

## 🧪 Development Tips

### Hot Module Replacement (HMR)

Vite provides instant HMR - changes appear immediately without full page reload.

### Type Safety

TypeScript ensures type safety. Key type definitions:
- `src/types/service.ts` - Service models
- `src/types/drift.ts` - Drift analysis models

### Data Fetching

TanStack Query handles data fetching with:
- Automatic caching
- Background refetching
- Loading states
- Error handling

Example:
```typescript
const { data, isLoading, error } = useServices();
```

### State Management

Zustand for global state (if needed):
```typescript
// src/store/appStore.ts
import { create } from 'zustand';

export const useAppStore = create((set) => ({
  theme: 'light',
  setTheme: (theme) => set({ theme }),
}));
```

## 🐛 Troubleshooting

### Port Already in Use

Change the port in `vite.config.ts`:
```typescript
server: {
  port: 5174, // Change to any available port
}
```

### API Connection Issues

1. Ensure FastAPI backend is running on http://localhost:3000
2. Check proxy configuration in `vite.config.ts`
3. Verify CORS is enabled on backend

### Build Errors

```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install

# Clean build
npm run build
```

## 📚 Resources

- [React Documentation](https://react.dev/)
- [TypeScript Documentation](https://www.typescriptlang.org/docs/)
- [Vite Documentation](https://vitejs.dev/)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [Shadcn/ui Documentation](https://ui.shadcn.com/)
- [TanStack Query Documentation](https://tanstack.com/query/latest)

## 🤝 Contributing

1. Follow the existing code structure
2. Use TypeScript for type safety
3. Follow Tailwind CSS conventions
4. Test in both dev and production builds
5. Ensure responsive design (mobile, tablet, desktop)

## 📄 License

Same as the parent project.


