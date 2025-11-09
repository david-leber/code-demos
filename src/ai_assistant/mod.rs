use anyhow::{Context, Result};
use serde::{Deserialize, Serialize};

use crate::models::{AIReview, CodeQuality, Lesson};

#[derive(Debug, Clone)]
pub struct AIAssistant {
    api_key: Option<String>,
    client: reqwest::Client,
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

impl AIAssistant {
    pub fn new(api_key: Option<String>) -> Self {
        Self {
            api_key,
            client: reqwest::Client::new(),
        }
    }

    pub async fn review_code(&self, code: &str, lesson: &Lesson) -> Result<AIReview> {
        // If no API key is provided, use a simple rule-based review
        if self.api_key.is_none() {
            return self.simple_review(code, lesson);
        }

        let prompt = self.build_review_prompt(code, lesson);

        let api_key = self.api_key.as_ref().unwrap();

        let request = ClaudeRequest {
            model: "claude-3-5-sonnet-20241022".to_string(),
            max_tokens: 1024,
            messages: vec![ClaudeMessage {
                role: "user".to_string(),
                content: prompt,
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
            tracing::warn!("Claude API error ({}): {}", status, error_text);
            return self.simple_review(code, lesson);
        }

        let claude_response: ClaudeResponse = response
            .json()
            .await
            .context("Failed to parse Claude API response")?;

        let feedback = claude_response
            .content
            .first()
            .map(|c| c.text.clone())
            .unwrap_or_else(|| "No feedback available".to_string());

        // Parse the response to extract structured feedback
        self.parse_ai_feedback(&feedback, lesson)
    }

    fn build_review_prompt(&self, code: &str, lesson: &Lesson) -> String {
        format!(
            r#"You are a helpful Python programming tutor. Review the following student code for a lesson.

Lesson: {}
Description: {}
Objectives: {}

Student Code:
```python
{}
```

Please provide:
1. Overall feedback on the code quality and correctness
2. Specific suggestions for improvement
3. Whether the code meets the lesson objectives
4. A code quality rating: Excellent, Good, NeedsImprovement, or Poor

Keep your feedback encouraging and constructive. Focus on helping the student learn."#,
            lesson.title,
            lesson.description,
            lesson.objectives.join(", "),
            code
        )
    }

    fn parse_ai_feedback(&self, feedback: &str, _lesson: &Lesson) -> Result<AIReview> {
        // Simple parsing - in production, you'd want more robust parsing
        let code_quality = if feedback.to_lowercase().contains("excellent") {
            CodeQuality::Excellent
        } else if feedback.to_lowercase().contains("good") {
            CodeQuality::Good
        } else if feedback.to_lowercase().contains("needs improvement") || feedback.to_lowercase().contains("poor") {
            CodeQuality::NeedsImprovement
        } else {
            CodeQuality::Good
        };

        let follows_objectives = !feedback.to_lowercase().contains("does not meet") &&
                                 !feedback.to_lowercase().contains("doesn't meet");

        // Extract suggestions (lines starting with numbers or bullets)
        let suggestions: Vec<String> = feedback
            .lines()
            .filter(|line| {
                line.trim().starts_with('-') ||
                line.trim().starts_with('•') ||
                line.trim().chars().next().map(|c| c.is_numeric()).unwrap_or(false)
            })
            .map(|s| s.trim().to_string())
            .collect();

        Ok(AIReview {
            feedback: feedback.to_string(),
            suggestions,
            code_quality,
            follows_lesson_objectives: follows_objectives,
        })
    }

    fn simple_review(&self, code: &str, lesson: &Lesson) -> Result<AIReview> {
        let mut suggestions = Vec::new();
        let mut quality_score = 0;

        // Simple heuristics
        if code.len() < 10 {
            suggestions.push("Your code seems quite short. Make sure you've completed all the requirements.".to_string());
        } else {
            quality_score += 1;
        }

        if !code.contains("def ") && lesson.objectives.iter().any(|obj| obj.to_lowercase().contains("function")) {
            suggestions.push("This lesson requires defining a function. Consider using 'def' to create one.".to_string());
        } else if code.contains("def ") {
            quality_score += 1;
        }

        if code.lines().count() > 1 {
            quality_score += 1;
        }

        let code_quality = match quality_score {
            3 => CodeQuality::Excellent,
            2 => CodeQuality::Good,
            1 => CodeQuality::NeedsImprovement,
            _ => CodeQuality::Poor,
        };

        let feedback = format!(
            "Code review for '{}': Your code has been submitted. {}",
            lesson.title,
            if suggestions.is_empty() {
                "Keep up the good work!"
            } else {
                "Here are some suggestions to improve your code."
            }
        );

        Ok(AIReview {
            feedback,
            suggestions,
            code_quality,
            follows_lesson_objectives: quality_score >= 2,
        })
    }
}
