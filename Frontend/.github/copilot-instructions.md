# FinFind Frontend - Copilot Instructions

## Project Overview
FinFind is a context-aware FinCommerce engine frontend built with Next.js 14+, TypeScript, and Tailwind CSS. It connects to a FastAPI backend for product search, recommendations, and user management.

## Tech Stack
- **Framework**: Next.js 14+ with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS + shadcn/ui components
- **State Management**: React Query (TanStack Query)
- **API Client**: Axios with custom hooks
- **Icons**: Lucide React

## Project Structure
```
Frontend/
├── app/                    # Next.js App Router pages
│   ├── page.tsx           # Home/Search page
│   ├── search/            # Search results
│   ├── product/[id]/      # Product details
│   ├── recommendations/   # Personalized recommendations
│   ├── profile/           # User profile
│   └── layout.tsx         # Root layout
├── components/
│   ├── ui/                # shadcn/ui components
│   ├── search/            # Search-related components
│   ├── product/           # Product-related components
│   └── layout/            # Layout components
├── hooks/                 # Custom React hooks
├── lib/                   # Utilities and API client
├── types/                 # TypeScript type definitions
└── public/                # Static assets
```

## Backend Connection
- API Base URL: `http://localhost:8000/api/v1`
- Endpoints are defined in `lib/api.ts`
- React Query hooks in `hooks/` directory

## Development Commands
```bash
npm run dev     # Start development server
npm run build   # Build for production
npm run lint    # Run ESLint
```

## Coding Guidelines
- Use TypeScript strict mode
- Follow React best practices (hooks, functional components)
- Use shadcn/ui components for consistent UI
- Implement proper loading and error states
- Add accessibility features (ARIA labels)
- Support dark mode with Tailwind classes
