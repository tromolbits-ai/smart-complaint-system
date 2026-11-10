use std::env;

#[derive(Clone, Debug)]
pub struct Config {
    pub database_url: String,
    pub server_port: u16,
    pub jwt_secret: String,
    pub upload_dir: String,
}

impl Config {
    pub fn from_env() -> Self {
        dotenvy::dotenv().ok();
        Self {
            database_url: env::var("DATABASE_URL")
                .unwrap_or_else(|_| "postgres://postgres:postgres@localhost:5432/scs_db".to_string()),
            server_port: env::var("PORT")
                .ok()
                .and_then(|p| p.parse().ok())
                .unwrap_or(8080),
            jwt_secret: env::var("JWT_SECRET")
                .unwrap_or_else(|_| "scs_bandarlampung_secret_jwt_key_2026".to_string()),
            upload_dir: env::var("UPLOAD_DIR")
                .unwrap_or_else(|_| "./static/uploads".to_string()),
        }
    }
}

