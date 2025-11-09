use anyhow::{Context, Result};
use std::collections::HashMap;
use std::fs;
use std::path::Path;

use crate::models::Lesson;

pub struct LessonManager {
    lessons: HashMap<String, Lesson>,
    lesson_order: Vec<String>,
}

impl LessonManager {
    pub fn new() -> Self {
        Self {
            lessons: HashMap::new(),
            lesson_order: Vec::new(),
        }
    }

    pub fn load_lessons<P: AsRef<Path>>(&mut self, lessons_dir: P) -> Result<()> {
        let lessons_dir = lessons_dir.as_ref();

        if !lessons_dir.exists() {
            tracing::warn!("Lessons directory does not exist: {:?}", lessons_dir);
            return Ok(());
        }

        let entries = fs::read_dir(lessons_dir)
            .context("Failed to read lessons directory")?;

        for entry in entries {
            let entry = entry?;
            let path = entry.path();

            if path.extension().and_then(|s| s.to_str()) == Some("yaml") ||
               path.extension().and_then(|s| s.to_str()) == Some("yml") {
                let content = fs::read_to_string(&path)
                    .with_context(|| format!("Failed to read lesson file: {:?}", path))?;

                let lesson: Lesson = serde_yaml::from_str(&content)
                    .with_context(|| format!("Failed to parse lesson file: {:?}", path))?;

                tracing::info!("Loaded lesson: {} - {}", lesson.id, lesson.title);
                self.lesson_order.push(lesson.id.clone());
                self.lessons.insert(lesson.id.clone(), lesson);
            }
        }

        // Sort lessons by ID for consistent ordering
        self.lesson_order.sort();

        Ok(())
    }

    pub fn get_lesson(&self, lesson_id: &str) -> Option<&Lesson> {
        self.lessons.get(lesson_id)
    }

    pub fn get_all_lessons(&self) -> Vec<&Lesson> {
        self.lesson_order
            .iter()
            .filter_map(|id| self.lessons.get(id))
            .collect()
    }

    pub fn get_next_lesson(&self, current_lesson_id: &str) -> Option<&Lesson> {
        let current_idx = self.lesson_order.iter().position(|id| id == current_lesson_id)?;
        let next_idx = current_idx + 1;

        if next_idx < self.lesson_order.len() {
            self.lessons.get(&self.lesson_order[next_idx])
        } else {
            None
        }
    }

    pub fn get_first_lesson(&self) -> Option<&Lesson> {
        self.lesson_order
            .first()
            .and_then(|id| self.lessons.get(id))
    }
}

impl Default for LessonManager {
    fn default() -> Self {
        Self::new()
    }
}
