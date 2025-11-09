mod ai_assistant;
mod executor;
mod lessons;
mod models;
mod tutor;
mod web;

use anyhow::Result;
use std::sync::Arc;
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};

use ai_assistant::AIAssistant;
use executor::CodeExecutor;
use lessons::LessonManager;
use tutor::InteractiveTutor;
use web::{create_router, AppState};

#[tokio::main]
async fn main() -> Result<()> {
    // Initialize tracing
    tracing_subscriber::registry()
        .with(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| "coding_tutor_ide=debug,tower_http=debug".into()),
        )
        .with(tracing_subscriber::fmt::layer())
        .init();

    tracing::info!("Starting Coding Tutor IDE...");

    // Load lessons
    let mut lesson_manager = LessonManager::new();
    lesson_manager.load_lessons("lessons_content")?;
    tracing::info!("Loaded {} lessons", lesson_manager.get_all_lessons().len());

    // Initialize code executor
    let code_executor = Arc::new(CodeExecutor::new()?);
    tracing::info!("Code executor initialized");

    let lesson_manager = Arc::new(lesson_manager);

    // Initialize AI assistant (checks for ANTHROPIC_API_KEY env var)
    let api_key = std::env::var("ANTHROPIC_API_KEY").ok();
    if api_key.is_some() {
        tracing::info!("Interactive AI tutor initialized with API key");
    } else {
        tracing::info!("Interactive AI tutor initialized in simple mode (no API key found)");
    }
    let ai_assistant = AIAssistant::new(api_key.clone());

    // Initialize interactive tutor
    let interactive_tutor = InteractiveTutor::new(
        api_key,
        lesson_manager.clone(),
        code_executor.clone(),
    );

    // Create app state
    let state = AppState {
        lesson_manager,
        code_executor,
        ai_assistant: Arc::new(ai_assistant),
        interactive_tutor: Arc::new(interactive_tutor),
    };

    // Build router
    let app = create_router(state);

    // Start server
    let port = std::env::var("PORT").unwrap_or_else(|_| "3000".to_string());
    let addr = format!("0.0.0.0:{}", port);
    let listener = tokio::net::TcpListener::bind(&addr).await?;

    tracing::info!("🚀 Server running at http://{}", addr);
    tracing::info!("📚 Open http://localhost:{}/static/index.html to start learning!", port);

    axum::serve(listener, app).await?;

    Ok(())
}
