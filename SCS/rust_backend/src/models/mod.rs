use serde::{Deserialize, Serialize};
use uuid::Uuid;
use chrono::{DateTime, Utc};

#[derive(Debug, Serialize, Deserialize, sqlx::FromRow)]
pub struct User {
    pub id: Uuid,
    pub full_name: String,
    pub email: String,
    pub phone: Option<String>,
    pub nik: Option<String>,
    #[serde(skip_serializing)]
    pub password_hash: String,
    pub is_active: bool,
    pub created_at: DateTime<Utc>,
}

#[derive(Debug, Serialize, Deserialize, sqlx::FromRow)]
pub struct Department {
    pub id: i32,
    pub name: String,
    pub code: String,
    pub area_code: Option<String>,
    pub description: Option<String>,
    pub is_active: bool,
}

#[derive(Debug, Serialize, Deserialize, sqlx::FromRow)]
pub struct Category {
    pub id: i32,
    pub name: String,
    pub code: String,
    pub description: Option<String>,
    pub default_priority: String,
    pub icon: Option<String>,
    pub default_dept_id: Option<i32>,
    pub is_active: bool,
}

#[derive(Debug, Serialize, Deserialize, sqlx::FromRow)]
pub struct Report {
    pub id: Uuid,
    pub ticket_no: String,
    pub reporter_id: Uuid,
    pub category_id: i32,
    pub title: String,
    pub description: String,
    pub address_text: String,
    pub district: String,
    pub status: String,
    pub priority: String,
    pub rejection_reason: Option<String>,
    pub clarification_request: Option<String>,
    pub is_anonymous: bool,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

#[derive(Debug, Serialize, Deserialize, sqlx::FromRow)]
pub struct ReportStatusHistory {
    pub id: Uuid,
    pub report_id: Uuid,
    pub old_status: Option<String>,
    pub new_status: String,
    pub changed_by: Uuid,
    pub note: Option<String>,
    pub changed_at: DateTime<Utc>,
}

#[derive(Debug, Serialize, Deserialize, sqlx::FromRow)]
pub struct Feedback {
    pub id: Uuid,
    pub report_id: Uuid,
    pub user_id: Uuid,
    pub rating: i32,
    pub comment: Option<String>,
    pub created_at: DateTime<Utc>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct Claims {
    pub sub: String,
    pub email: String,
    pub name: String,
    pub roles: Vec<String>,
    pub exp: usize,
}

