FROM node:20-alpine AS builder

WORKDIR /app

# Copy bộ cài đặt packages
COPY package*.json ./
RUN npm install

# Copy toàn bộ source code
COPY . .

# Build Next.js
RUN npm run build

# Chạy bản production siêu nhẹ
FROM node:20-alpine AS runner
WORKDIR /app

# Khởi tạo quyền user bảo mật (không chạy bằng quyền root)
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json

USER nextjs

EXPOSE 3000

CMD ["npm", "start"]
