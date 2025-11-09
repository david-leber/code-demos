use axum::{
    extract::{Path, State},
    http::StatusCode,
    response::Json,
    routing::{get, post},
    Router,
};
use serde::{Deserialize, Serialize};
use std::sync::Arc;
use tower_http::services::ServeDir;

use crate::ai_assistant::AIAssistant;
use crate::executor::CodeExecutor;
use crate::lessons::LessonManager;
use crate::tutor::InteractiveTutor;
use crate::models::{AIReview, ExecutionResult, Lesson, TutorRequest, TutorResponse};

#[derive(Clone)]
pub struct AppState {
    pub lesson_manager: Arc<LessonManager>,
    pub code_executor: Arc<CodeExecutor>,
    pub ai_assistant: Arc<AIAssistant>,
    pub interactive_tutor: Arc<InteractiveTutor>,
}

pub fn create_router(state: AppState) -> Router {
    Router::new()
        .route("/", get(index_handler))
        .route("/api/lessons", get(get_lessons))
        .route("/api/lessons/:id", get(get_lesson))
        .route("/api/execute", post(execute_code))
        .route("/api/review", post(review_code))
        .route("/api/tutor/interact", post(tutor_interact))
        .nest_service("/static", ServeDir::new("static"))
        .with_state(state)
}

async fn index_handler() -> &'static str {
    "Coding Tutor IDE - Navigate to /static/index.html"
}

#[derive(Debug, Serialize)]
struct LessonsResponse {
    lessons: Vec<LessonSummary>,
}

#[derive(Debug, Serialize)]
struct LessonSummary {
    id: String,
    title: String,
    description: String,
}

async fn get_lessons(State(state): State<AppState>) -> Json<LessonsResponse> {
    let lessons = state
        .lesson_manager
        .get_all_lessons()
        .iter()
        .map(|lesson| LessonSummary {
            id: lesson.id.clone(),
            title: lesson.title.clone(),
            description: lesson.description.clone(),
        })
        .collect();

    Json(LessonsResponse { lessons })
}

async fn get_lesson(
    State(state): State<AppState>,
    Path(id): Path<String>,
) -> Result<Json<Lesson>, StatusCode> {
    state
        .lesson_manager
        .get_lesson(&id)
        .cloned()
        .map(Json)
        .ok_or(StatusCode::NOT_FOUND)
}

#[derive(Debug, Deserialize)]
struct ExecuteRequest {
    code: String,
    lesson_id: Option<String>,
    exercise_id: Option<String>,
}

async fn execute_code(
    State(state): State<AppState>,
    Json(request): Json<ExecuteRequest>,
) -> Result<Json<ExecutionResult>, (StatusCode, String)> {
    // If there's a lesson and exercise, run tests
    if let (Some(lesson_id), Some(exercise_id)) = (request.lesson_id, request.exercise_id) {
        let lesson = state
            .lesson_manager
            .get_lesson(&lesson_id)
            .ok_or((StatusCode::NOT_FOUND, "Lesson not found".to_string()))?;

        let exercise = lesson
            .exercises
            .iter()
            .find(|e| e.id == exercise_id)
            .ok_or((StatusCode::NOT_FOUND, "Exercise not found".to_string()))?;

        let result = state
            .code_executor
            .execute_with_tests(&request.code, &exercise.test_code)
            .await
            .map_err(|e| (StatusCode::INTERNAL_SERVER_ERROR, e.to_string()))?;

        Ok(Json(result))
    } else {
        // Just run the code without tests
        let result = state
            .code_executor
            .execute_code(&request.code, 10)
            .await
            .map_err(|e| (StatusCode::INTERNAL_SERVER_ERROR, e.to_string()))?;

        Ok(Json(result))
    }
}

#[derive(Debug, Deserialize)]
struct ReviewRequest {
    code: String,
    lesson_id: String,
}

async fn review_code(
    State(state): State<AppState>,
    Json(request): Json<ReviewRequest>,
) -> Result<Json<AIReview>, (StatusCode, String)> {
    let lesson = state
        .lesson_manager
        .get_lesson(&request.lesson_id)
        .ok_or((StatusCode::NOT_FOUND, "Lesson not found".to_string()))?;

    let review = state
        .ai_assistant
        .review_code(&request.code, lesson)
        .await
        .map_err(|e| (StatusCode::INTERNAL_SERVER_ERROR, e.to_string()))?;

    Ok(Json(review))
}

async fn tutor_interact(
    State(state): State<AppState>,
    Json(request): Json<TutorRequest>,
) -> Result<Json<TutorResponse>, (StatusCode, String)> {
    let response = state
        .interactive_tutor
        .handle_request(request)
        .await
        .map_err(|e| (StatusCode::INTERNAL_SERVER_ERROR, e.to_string()))?;

    Ok(Json(response))
}
