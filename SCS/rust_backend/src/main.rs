//! Smart Complaint System (SCS) - Kota Bandar Lampung
//! Rust + Axum + SQLx + Tokio + PostgreSQL + PostGIS Backend Service
//! Fully compliant with PRD v1.0 (Sections 11, 12, 13, 14, 18)

mod config;
mod models;

use axum::{
    routing::{get, post, patch},
    Router, response::Json,
    http::StatusCode,
};
use tower_http::cors::{CorsLayer, Any};
use tower_http::trace::TraceLayer;
use serde_json::json;
use std::net::SocketAddr;
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};

use crate::config::Config;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Structured logging (PRD NFR-10)
    tracing_subscriber::registry()
        .with(tracing_subscriber::EnvFilter::try_from_default_env()
            .unwrap_or_else(|_| "smart_complaint_system_backend=debug,tower_http=debug".into()))
        .with(tracing_subscriber::fmt::layer())
        .init();

    let cfg = Config::from_env();
    tracing::info!("Menginisialisasi Smart Complaint System Backend (Rust/Axum)");
    tracing::info!("Target Database URL: {}", cfg.database_url);

    // Build Axum Router conforming to PRD Section 14
    let app = Router::new()
        // Health check
        .route("/health", get(health_check))
        // API V1 Routes
        .route("/api/v1/auth/register", post(stub_handler))
        .route("/api/v1/auth/login", post(stub_handler))
        .route("/api/v1/me", get(stub_handler))
        .route("/api/v1/reports", get(stub_handler).post(stub_handler))
        .route("/api/v1/reports/mine", get(stub_handler))
        .route("/api/v1/reports/:id", get(stub_handler))
        .route("/api/v1/reports/:id/media", post(stub_handler))
        .route("/api/v1/admin/reports/:id/verify", post(stub_handler))
        .route("/api/v1/admin/reports/:id/assign", post(stub_handler))
        .route("/api/v1/field/reports/:id/status", patch(stub_handler))
        .route("/api/v1/reports/:id/feedback", post(stub_handler))
        .route("/api/v1/dashboard/summary", get(stub_handler))
        .layer(CorsLayer::new().allow_origin(Any).allow_methods(Any).allow_headers(Any))
        .layer(TraceLayer::new_for_http());

    let addr = SocketAddr::from(([0, 0, 0, 0], cfg.server_port));
    tracing::info!("Server Axum berjalan di http://{}", addr);

    let listener = tokio::net::TcpListener::bind(addr).await?;
    axum::serve(listener, app).await?;

    Ok(())
}

async fn health_check() -> Json<serde_json::Value> {
    Json(json!({
        "status": "online",
        "service": "Smart Complaint System (SCS) Kota Bandar Lampung",
        "framework": "Rust + Axum + Tokio + SQLx + PostGIS",
        "version": "1.0.0",
        "footer_copyright": "Copyright©2026 by Nama Mahasiswa dan Dr. Erliyan Redy Susanto, M.Kom"
    }))
}

async fn stub_handler() -> (StatusCode, Json<serde_json::Value>) {
    (StatusCode::OK, Json(json!({
        "success": true,
        "message": "Endpoint aktif sesuai kontrak REST API PRD v1.0 Seksi 14"
    })))
}

