use serde::{Deserialize, Serialize};
use uuid::Uuid;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Lesson {
    pub id: String,
    pub title: String,
    pub description: String,
    pub objectives: Vec<String>,
    pub concepts: Vec<String>,  // Key concepts to teach
    pub examples: Vec<String>,  // Example code snippets for teaching

    // Optional for backward compatibility
    #[serde(default)]
    pub starter_code: String,
    #[serde(default)]
    pub exercises: Vec<Exercise>,
    #[serde(default)]
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
    pub teaching_phase: TeachingPhase,
    pub conversation_history: Vec<Message>,
    pub current_challenge: Option<Challenge>,
    pub completed_exercises: Vec<String>,
    pub code_history: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum TeachingPhase {
    Introduction,   // AI introduces the lesson
    Teaching,       // AI teaches concepts
    Challenge,      // Student attempts challenge
    Helping,        // AI provides Socratic guidance
    Walkthrough,    // AI walks through solution
    NewChallenge,   // New challenge after walkthrough
    Mastery,        // Student demonstrated mastery
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Challenge {
    pub description: String,
    pub validation_hints: Vec<String>,
    pub hints_given: u32,
    pub walkthrough_used: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Message {
    pub role: MessageRole,
    pub content: String,
    pub timestamp: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum MessageRole {
    Tutor,
    Student,
    System,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TutorRequest {
    pub session_id: Uuid,
    pub lesson_id: String,
    pub message: Option<String>,
    pub code: Option<String>,
    pub request_type: TutorRequestType,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum TutorRequestType {
    StartLesson,
    SendMessage,
    SubmitCode,
    RequestHint,
    RequestWalkthrough,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TutorResponse {
    pub message: String,
    pub phase: TeachingPhase,
    pub code_result: Option<ExecutionResult>,
    pub show_new_challenge: bool,
}
