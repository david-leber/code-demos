use anyhow::{Context, Result};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::RwLock;
use uuid::Uuid;

use crate::executor::CodeExecutor;
use crate::lessons::LessonManager;
use crate::models::*;

pub struct InteractiveTutor {
    api_key: Option<String>,
    client: reqwest::Client,
    sessions: Arc<RwLock<HashMap<Uuid, SessionState>>>,
    lesson_manager: Arc<LessonManager>,
    code_executor: Arc<CodeExecutor>,
}

#[derive(Debug, Serialize)]
struct ClaudeRequest {
    model: String,
    max_tokens: u32,
    messages: Vec<ClaudeMessage>,
}

#[derive(Debug, Serialize, Deserialize)]
struct ClaudeMessage {
    role: String,
    content: String,
}

#[derive(Debug, Deserialize)]
struct ClaudeResponse {
    content: Vec<ClaudeContent>,
}

#[derive(Debug, Deserialize)]
struct ClaudeContent {
    text: String,
}

impl InteractiveTutor {
    pub fn new(
        api_key: Option<String>,
        lesson_manager: Arc<LessonManager>,
        code_executor: Arc<CodeExecutor>,
    ) -> Self {
        Self {
            api_key,
            client: reqwest::Client::new(),
            sessions: Arc::new(RwLock::new(HashMap::new())),
            lesson_manager,
            code_executor,
        }
    }

    pub async fn handle_request(&self, request: TutorRequest) -> Result<TutorResponse> {
        match request.request_type {
            TutorRequestType::StartLesson => self.start_lesson(request).await,
            TutorRequestType::SendMessage => self.handle_message(request).await,
            TutorRequestType::SubmitCode => self.handle_code_submission(request).await,
            TutorRequestType::RequestHint => self.provide_hint(request).await,
            TutorRequestType::RequestWalkthrough => self.provide_walkthrough(request).await,
        }
    }

    async fn start_lesson(&self, request: TutorRequest) -> Result<TutorResponse> {
        let lesson = self
            .lesson_manager
            .get_lesson(&request.lesson_id)
            .context("Lesson not found")?;

        let mut sessions = self.sessions.write().await;

        let session = SessionState {
            session_id: request.session_id,
            current_lesson_id: request.lesson_id.clone(),
            teaching_phase: TeachingPhase::Introduction,
            conversation_history: Vec::new(),
            current_challenge: None,
            completed_exercises: Vec::new(),
            code_history: Vec::new(),
        };

        sessions.insert(request.session_id, session);
        drop(sessions);

        // Generate introduction
        let intro_message = self.generate_introduction(lesson).await?;

        self.add_message(request.session_id, MessageRole::Tutor, &intro_message)
            .await;

        Ok(TutorResponse {
            message: intro_message,
            phase: TeachingPhase::Introduction,
            code_result: None,
            show_new_challenge: false,
        })
    }

    async fn handle_message(&self, request: TutorRequest) -> Result<TutorResponse> {
        let student_message = request.message.context("Message is required")?;

        self.add_message(request.session_id, MessageRole::Student, &student_message)
            .await;

        let sessions = self.sessions.read().await;
        let session = sessions
            .get(&request.session_id)
            .context("Session not found")?
            .clone();
        drop(sessions);

        let lesson = self
            .lesson_manager
            .get_lesson(&session.current_lesson_id)
            .context("Lesson not found")?;

        let response_message = match session.teaching_phase {
            TeachingPhase::Introduction | TeachingPhase::Teaching => {
                self.continue_teaching(&session, lesson, &student_message)
                    .await?
            }
            TeachingPhase::Challenge | TeachingPhase::NewChallenge => {
                self.provide_socratic_guidance(&session, lesson, &student_message)
                    .await?
            }
            _ => "Please submit your code to continue.".to_string(),
        };

        self.add_message(request.session_id, MessageRole::Tutor, &response_message)
            .await;

        Ok(TutorResponse {
            message: response_message,
            phase: session.teaching_phase.clone(),
            code_result: None,
            show_new_challenge: false,
        })
    }

    async fn handle_code_submission(&self, request: TutorRequest) -> Result<TutorResponse> {
        let code = request.code.context("Code is required")?;

        let sessions = self.sessions.read().await;
        let session = sessions
            .get(&request.session_id)
            .context("Session not found")?
            .clone();
        drop(sessions);

        let lesson = self
            .lesson_manager
            .get_lesson(&session.current_lesson_id)
            .context("Lesson not found")?;

        // Execute the code
        let exec_result = self.code_executor.execute_code(&code, 10).await?;

        // Evaluate the submission
        let (feedback, new_phase, show_new_challenge) = self
            .evaluate_submission(&session, lesson, &code, &exec_result)
            .await?;

        // Update session phase
        self.update_phase(request.session_id, new_phase.clone())
            .await;

        self.add_message(request.session_id, MessageRole::Tutor, &feedback)
            .await;

        Ok(TutorResponse {
            message: feedback,
            phase: new_phase,
            code_result: Some(exec_result),
            show_new_challenge,
        })
    }

    async fn provide_hint(&self, request: TutorRequest) -> Result<TutorResponse> {
        let sessions = self.sessions.read().await;
        let session = sessions
            .get(&request.session_id)
            .context("Session not found")?
            .clone();
        drop(sessions);

        let lesson = self
            .lesson_manager
            .get_lesson(&session.current_lesson_id)
            .context("Lesson not found")?;

        let hint = self.generate_socratic_hint(&session, lesson).await?;

        // Increment hints given
        if let Some(challenge) = &session.current_challenge {
            let mut updated_challenge = challenge.clone();
            updated_challenge.hints_given += 1;
            self.update_challenge(request.session_id, updated_challenge)
                .await;
        }

        self.add_message(request.session_id, MessageRole::Tutor, &hint)
            .await;

        Ok(TutorResponse {
            message: hint,
            phase: TeachingPhase::Helping,
            code_result: None,
            show_new_challenge: false,
        })
    }

    async fn provide_walkthrough(&self, request: TutorRequest) -> Result<TutorResponse> {
        let sessions = self.sessions.read().await;
        let session = sessions
            .get(&request.session_id)
            .context("Session not found")?
            .clone();
        drop(sessions);

        let lesson = self
            .lesson_manager
            .get_lesson(&session.current_lesson_id)
            .context("Lesson not found")?;

        let walkthrough = self.generate_walkthrough(&session, lesson).await?;

        // Mark walkthrough as used - this triggers new challenge requirement
        if let Some(challenge) = &session.current_challenge {
            let mut updated_challenge = challenge.clone();
            updated_challenge.walkthrough_used = true;
            self.update_challenge(request.session_id, updated_challenge)
                .await;
        }

        self.update_phase(request.session_id, TeachingPhase::Walkthrough)
            .await;

        self.add_message(request.session_id, MessageRole::Tutor, &walkthrough)
            .await;

        Ok(TutorResponse {
            message: walkthrough,
            phase: TeachingPhase::Walkthrough,
            code_result: None,
            show_new_challenge: true, // Indicate new challenge will be needed
        })
    }

    async fn generate_introduction(&self, lesson: &Lesson) -> Result<String> {
        if self.api_key.is_none() {
            return Ok(self.simple_introduction(lesson));
        }

        let prompt = format!(
            r#"You are an enthusiastic and encouraging Python programming tutor.

Introduce this lesson to a beginner:

Lesson: {}
Description: {}
Objectives: {}

Provide a warm, encouraging introduction that:
1. Explains what they'll learn
2. Why it's useful
3. Gets them excited to start
4. Is conversational and friendly

Keep it to 2-3 paragraphs. End by asking if they're ready to learn about the first concept."#,
            lesson.title,
            lesson.description,
            lesson.objectives.join(", ")
        );

        self.call_claude(&prompt).await
    }

    async fn continue_teaching(
        &self,
        session: &SessionState,
        lesson: &Lesson,
        student_message: &str,
    ) -> Result<String> {
        if self.api_key.is_none() {
            return Ok(self.simple_teaching_response(lesson, student_message));
        }

        let conversation_context = self.build_conversation_context(session);

        let prompt = format!(
            r#"You are a patient Python programming tutor using the Socratic method.

Lesson: {}
Objectives: {}
Key Concepts: {}

Previous conversation:
{}

Student's latest message: "{}"

Continue teaching about these concepts. When you've covered the key concepts and the student seems ready, present them with a coding challenge to demonstrate their understanding.

IMPORTANT:
- Teach one concept at a time
- Use simple examples
- Check for understanding
- When ready, transition to presenting a challenge
- The challenge should test if they understand the objectives

Your response:"#,
            lesson.title,
            lesson.objectives.join(", "),
            lesson.concepts.join(", "),
            conversation_context,
            student_message
        );

        let response = self.call_claude(&prompt).await?;

        // Check if AI is presenting a challenge
        if response.to_lowercase().contains("challenge")
            || response.to_lowercase().contains("try to")
            || response.to_lowercase().contains("your task")
        {
            // Transition to challenge phase
            let challenge = Challenge {
                description: response.clone(),
                validation_hints: Vec::new(),
                hints_given: 0,
                walkthrough_used: false,
            };

            self.update_challenge(session.session_id, challenge).await;
            self.update_phase(session.session_id, TeachingPhase::Challenge)
                .await;
        }

        Ok(response)
    }

    async fn provide_socratic_guidance(
        &self,
        session: &SessionState,
        lesson: &Lesson,
        student_message: &str,
    ) -> Result<String> {
        if self.api_key.is_none() {
            return Ok(
                "Think about the problem step by step. What do you need to do first?".to_string(),
            );
        }

        let challenge_desc = session
            .current_challenge
            .as_ref()
            .map(|c| c.description.clone())
            .unwrap_or_default();

        let conversation_context = self.build_conversation_context(session);

        let prompt = format!(
            r#"You are a Python tutor helping a student solve a coding challenge using the Socratic method.

Lesson Objectives: {}
Challenge: {}

Conversation history:
{}

Student says: "{}"

Provide guidance using the Socratic method:
- Ask guiding questions rather than giving answers
- Help them think through the problem
- Suggest approaches without solving it for them
- Encourage them to try things
- NEVER give them the direct answer or complete solution

If they seem very stuck, remind them they can request a hint or walkthrough.

Your response:"#,
            lesson.objectives.join(", "),
            challenge_desc,
            conversation_context,
            student_message
        );

        self.call_claude(&prompt).await
    }

    async fn generate_socratic_hint(&self, session: &SessionState, lesson: &Lesson) -> Result<String> {
        if self.api_key.is_none() {
            return Ok("Try breaking down the problem into smaller steps. What's the first thing you need to do?".to_string());
        }

        let challenge_desc = session
            .current_challenge
            .as_ref()
            .map(|c| c.description.clone())
            .unwrap_or_default();

        let hints_given = session
            .current_challenge
            .as_ref()
            .map(|c| c.hints_given)
            .unwrap_or(0);

        let prompt = format!(
            r#"You are providing a hint to a student stuck on a Python coding challenge.

Challenge: {}
Hints already given: {}

Provide a helpful hint that:
- Points them in the right direction
- Doesn't give away the answer
- Focuses on ONE specific aspect they should consider
- Gets progressively more specific if multiple hints have been given

Your hint:"#,
            challenge_desc, hints_given
        );

        self.call_claude(&prompt).await
    }

    async fn generate_walkthrough(&self, session: &SessionState, lesson: &Lesson) -> Result<String> {
        if self.api_key.is_none() {
            return Ok("Let me walk you through this step by step. Since I've helped you through this, I'll give you a new challenge to demonstrate your understanding.".to_string());
        }

        let challenge_desc = session
            .current_challenge
            .as_ref()
            .map(|c| c.description.clone())
            .unwrap_or_default();

        let prompt = format!(
            r#"You are walking a student through solving a Python coding challenge step-by-step.

Lesson: {}
Challenge: {}

Provide a step-by-step walkthrough that:
1. Breaks down the problem
2. Explains each step of the solution
3. Shows the code with detailed explanations
4. Ends by explaining that since you walked them through this, you'll now give them a NEW, DIFFERENT challenge to prove they understood

Your walkthrough:"#,
            lesson.title, challenge_desc
        );

        self.call_claude(&prompt).await
    }

    async fn evaluate_submission(
        &self,
        session: &SessionState,
        lesson: &Lesson,
        code: &str,
        exec_result: &ExecutionResult,
    ) -> Result<(String, TeachingPhase, bool)> {
        // Check if walkthrough was used
        let walkthrough_used = session
            .current_challenge
            .as_ref()
            .map(|c| c.walkthrough_used)
            .unwrap_or(false);

        if !exec_result.success {
            let feedback = format!(
                "Your code has an error:\n{}\n\nDon't worry! Errors are part of learning. Can you figure out what went wrong? I'm here to help if you need it.",
                exec_result.error.as_ref().unwrap_or(&"Unknown error".to_string())
            );
            return Ok((feedback, TeachingPhase::Challenge, false));
        }

        // If walkthrough was used, generate new challenge
        if walkthrough_used {
            let new_challenge_response = self
                .generate_new_challenge(session, lesson, code)
                .await?;
            return Ok((
                new_challenge_response,
                TeachingPhase::NewChallenge,
                true,
            ));
        }

        // Otherwise, evaluate if they demonstrated mastery
        let evaluation = self.evaluate_mastery(session, lesson, code, exec_result)
            .await?;

        if evaluation.0 {
            Ok((
                evaluation.1,
                TeachingPhase::Mastery,
                false,
            ))
        } else {
            Ok((
                evaluation.1,
                TeachingPhase::Challenge,
                false,
            ))
        }
    }

    async fn evaluate_mastery(
        &self,
        session: &SessionState,
        lesson: &Lesson,
        code: &str,
        exec_result: &ExecutionResult,
    ) -> Result<(bool, String)> {
        if self.api_key.is_none() {
            return Ok((
                true,
                format!(
                    "Great job! Your code works! Output:\n{}\n\nYou've demonstrated understanding of this lesson!",
                    exec_result.output
                ),
            ));
        }

        let challenge_desc = session
            .current_challenge
            .as_ref()
            .map(|c| c.description.clone())
            .unwrap_or_default();

        let prompt = format!(
            r#"You are evaluating a student's Python code for a learning challenge.

Lesson Objectives: {}
Challenge: {}

Student's Code:
```python
{}
```

Output: {}

Evaluate if the student has demonstrated understanding of the lesson objectives:
1. Does the code solve the challenge correctly?
2. Does it show understanding of the key concepts?
3. Is the approach reasonable for a beginner?

Respond in this format:
MASTERY: [YES or NO]
FEEDBACK: [Your encouraging feedback]

If YES: Congratulate them and explain what they did well
If NO: Provide constructive feedback on what to improve, without giving the answer"#,
            lesson.objectives.join(", "),
            challenge_desc,
            code,
            exec_result.output
        );

        let response = self.call_claude(&prompt).await?;

        let mastered = response.to_uppercase().contains("MASTERY: YES");
        let feedback = response
            .lines()
            .skip_while(|line| !line.starts_with("FEEDBACK:"))
            .skip(1)
            .collect::<Vec<_>>()
            .join("\n")
            .trim()
            .to_string();

        Ok((mastered, feedback))
    }

    async fn generate_new_challenge(
        &self,
        session: &SessionState,
        lesson: &Lesson,
        previous_code: &str,
    ) -> Result<String> {
        if self.api_key.is_none() {
            return Ok(format!(
                "Great! Now try creating a similar solution but for a different scenario. You've got this!"
            ));
        }

        let old_challenge = session
            .current_challenge
            .as_ref()
            .map(|c| c.description.clone())
            .unwrap_or_default();

        let prompt = format!(
            r#"You are a Python tutor. The student needed a walkthrough for this challenge:

Previous Challenge: {}

Now generate a NEW, DIFFERENT challenge that:
1. Tests the SAME concepts and objectives: {}
2. Is similar in difficulty
3. Uses a different scenario or example
4. Is NOT the same as the previous challenge

Explain that since they needed help with the first challenge, this new one will let them demonstrate they truly understand the concept.

Your new challenge:"#,
            old_challenge,
            lesson.objectives.join(", ")
        );

        let new_challenge_text = self.call_claude(&prompt).await?;

        // Create new challenge
        let challenge = Challenge {
            description: new_challenge_text.clone(),
            validation_hints: Vec::new(),
            hints_given: 0,
            walkthrough_used: false,
        };

        self.update_challenge(session.session_id, challenge).await;

        Ok(new_challenge_text)
    }

    fn simple_introduction(&self, lesson: &Lesson) -> String {
        format!(
            "Welcome to {}!\n\n{}\n\nIn this lesson, you'll learn:\n{}\n\nAre you ready to get started?",
            lesson.title,
            lesson.description,
            lesson.objectives
                .iter()
                .map(|obj| format!("• {}", obj))
                .collect::<Vec<_>>()
                .join("\n")
        )
    }

    fn simple_teaching_response(&self, lesson: &Lesson, _message: &str) -> String {
        format!(
            "Let's learn about {}. Try writing some code to practice the concepts.",
            lesson.title
        )
    }

    async fn call_claude(&self, prompt: &str) -> Result<String> {
        let api_key = self
            .api_key
            .as_ref()
            .context("API key not available")?;

        let request = ClaudeRequest {
            model: "claude-3-5-sonnet-20241022".to_string(),
            max_tokens: 2048,
            messages: vec![ClaudeMessage {
                role: "user".to_string(),
                content: prompt.to_string(),
            }],
        };

        let response = self
            .client
            .post("https://api.anthropic.com/v1/messages")
            .header("x-api-key", api_key)
            .header("anthropic-version", "2023-06-01")
            .header("content-type", "application/json")
            .json(&request)
            .send()
            .await
            .context("Failed to send request to Claude API")?;

        if !response.status().is_success() {
            let status = response.status();
            let error_text = response.text().await.unwrap_or_default();
            anyhow::bail!("Claude API error ({}): {}", status, error_text);
        }

        let claude_response: ClaudeResponse = response
            .json()
            .await
            .context("Failed to parse Claude API response")?;

        Ok(claude_response
            .content
            .first()
            .map(|c| c.text.clone())
            .unwrap_or_else(|| "I'm having trouble responding right now.".to_string()))
    }

    fn build_conversation_context(&self, session: &SessionState) -> String {
        session
            .conversation_history
            .iter()
            .take(10) // Last 10 messages for context
            .map(|msg| {
                let role = match msg.role {
                    MessageRole::Tutor => "Tutor",
                    MessageRole::Student => "Student",
                    MessageRole::System => "System",
                };
                format!("{}: {}", role, msg.content)
            })
            .collect::<Vec<_>>()
            .join("\n")
    }

    async fn add_message(&self, session_id: Uuid, role: MessageRole, content: &str) {
        let mut sessions = self.sessions.write().await;
        if let Some(session) = sessions.get_mut(&session_id) {
            session.conversation_history.push(Message {
                role,
                content: content.to_string(),
                timestamp: std::time::SystemTime::now()
                    .duration_since(std::time::UNIX_EPOCH)
                    .unwrap()
                    .as_secs(),
            });
        }
    }

    async fn update_phase(&self, session_id: Uuid, phase: TeachingPhase) {
        let mut sessions = self.sessions.write().await;
        if let Some(session) = sessions.get_mut(&session_id) {
            session.teaching_phase = phase;
        }
    }

    async fn update_challenge(&self, session_id: Uuid, challenge: Challenge) {
        let mut sessions = self.sessions.write().await;
        if let Some(session) = sessions.get_mut(&session_id) {
            session.current_challenge = Some(challenge);
        }
    }
}
