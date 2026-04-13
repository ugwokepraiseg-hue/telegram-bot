# Workspace

## Overview

pnpm workspace monorepo using TypeScript. Each package manages its own dependencies.

## Stack

- **Monorepo tool**: pnpm workspaces
- **Node.js version**: 24
- **Package manager**: pnpm
- **TypeScript version**: 5.9
- **API framework**: Express 5
- **Database**: PostgreSQL + Drizzle ORM
- **Validation**: Zod (`zod/v4`), `drizzle-zod`
- **API codegen**: Orval (from OpenAPI spec)
- **Build**: esbuild (CJS bundle)

## Key Commands

- `pnpm run typecheck` — full typecheck across all packages
- `pnpm run build` — typecheck + build all packages
- `pnpm --filter @workspace/api-spec run codegen` — regenerate API hooks and Zod schemas from OpenAPI spec
- `pnpm --filter @workspace/db run push` — push DB schema changes (dev only)
- `pnpm --filter @workspace/api-server run dev` — run API server locally

See the `pnpm-workspace` skill for workspace structure, TypeScript setup, and package details.

## Telegram Bot (@majortrendprobot)

- **Package**: `@workspace/telegram-bot` in `artifacts/telegram-bot/`
- **Runtime**: Node.js with `node-telegram-bot-api`
- **Admin ID**: 8463629333 (receives all user messages)
- **Features**: Main menu with Buy, Sell, Import Wallet, Add Assets, Wallet Balance, Wallet Management, Portfolio, Copy Trading, Limit Order, Refer & Earn, Help, Signals, Language, Settings
- **Robustness**: Auto-restart on errors, graceful shutdown, heartbeat logging every 5 min
- **Secret**: `TELEGRAM_BOT_TOKEN` (stored in Replit Secrets)
- **Workflow**: "Telegram Bot" runs `pnpm --filter @workspace/telegram-bot run start`
