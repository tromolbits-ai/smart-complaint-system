# ========================================================
# Dockerfile: Smart Complaint System (Rust + Axum)
# ========================================================
FROM rust:1.78-bookworm as builder

WORKDIR /usr/src/app
COPY Cargo.toml Cargo.lock* ./
RUN mkdir src && echo "fn main() {}" > src/main.rs && cargo build --release || true

COPY . .
RUN cargo build --release

# Production Runtime
FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y ca-certificates libssl3 postgresql-client && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY --from=builder /usr/src/app/target/release/smart-complaint-system-backend /app/scs-server
COPY --from=builder /usr/src/app/migrations /app/migrations

EXPOSE 8080
ENV PORT=8080
CMD ["/app/scs-server"]

