use serde::{Deserialize, Serialize};
use uuid::Uuid;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Lesson {
    pub id: String,
    pub title: String,
    pub description: String,
    pub objectives: Vec<String>,
    pub starter_code: String,
    pub exercises: Vec<Exercise>,
    pub hints: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Exercise {
    pub id: String,
    pub description: String,
    pub test_code: String,
    pub solution_example: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CodeSubmission {
    pub code: String,
    pub lesson_id: String,
    pub exercise_id: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExecutionResult {
    pub success: bool,
    pub output: String,
    pub error: Option<String>,
    pub execution_time_ms: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AIReview {
    pub feedback: String,
    pub suggestions: Vec<String>,
    pub code_quality: CodeQuality,
    pub follows_lesson_objectives: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum CodeQuality {
    Excellent,
    Good,
    NeedsImprovement,
    Poor,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SessionState {
    pub session_id: Uuid,
    pub current_lesson_id: String,
    pub completed_exercises: Vec<String>,
    pub code_history: Vec<String>,
}
